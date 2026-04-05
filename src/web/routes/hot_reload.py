"""
PyAgent Web服务 - 热更新API路由

提供热更新功能，支持通过上传zip文件进行无缝更新。
"""

import zipfile
import shutil
import importlib
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hot-reload", tags=["hot-reload"])

_base_path: Optional[Path] = None
_manager: Optional["HotReloadManager"] = None


def init_hot_reload(base_path: Path) -> None:
    """初始化热更新管理器"""
    global _base_path, _manager
    _base_path = base_path
    _manager = HotReloadManager(base_path)


class HotReloadManager:
    """热更新管理器"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.backup_path = base_path / ".backup"
        self.temp_path = base_path / ".temp"
        self.current_version: Optional[str] = None
        self.update_status: dict[str, Any] = {
            "updating": False,
            "progress": 0,
            "message": "",
            "last_update": None,
            "error": None
        }
        self._load_version()

    def _load_version(self) -> None:
        """加载当前版本"""
        version_file = self.base_path / "pyproject.toml"
        if version_file.exists():
            content = version_file.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("version"):
                    self.current_version = line.split('"')[1] if '"' in line else "unknown"
                    break

    def validate_package(self, zip_path: Path) -> tuple[bool, str]:
        """验证更新包"""
        if not zip_path.exists():
            return False, "更新包不存在"

        if not zipfile.is_zipfile(zip_path):
            return False, "不是有效的zip文件"

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                namelist = zf.namelist()
                has_src = any(n.startswith('src/') for n in namelist)
                if not has_src:
                    return False, "更新包必须包含src目录"
            return True, "验证通过"
        except Exception as e:
            return False, f"验证失败: {str(e)}"

    async def backup_current(self) -> Optional[Path]:
        """备份当前版本"""
        if not self.backup_path.exists():
            self.backup_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / f"backup_{timestamp}"

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            src_path = self.base_path / "src"
            if src_path.exists():
                shutil.copytree(src_path, backup_dir / "src", dirs_exist_ok=True)
            
            pyproject = self.base_path / "pyproject.toml"
            if pyproject.exists():
                shutil.copy2(pyproject, backup_dir / "pyproject.toml")
            
            config_path = self.base_path / "config"
            if config_path.exists():
                shutil.copytree(config_path, backup_dir / "config", dirs_exist_ok=True)
            
            logger.info(f"备份完成: {backup_dir}")
            return backup_dir
        except Exception as e:
            logger.error(f"备份失败: {e}")
            return None

    async def apply_update(self, zip_path: Path) -> tuple[bool, list[str]]:
        """应用更新"""
        updated_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    if member.endswith('/'):
                        continue
                    
                    target_path = self.base_path / member
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zf.open(member) as source:
                        content = source.read()
                        target_path.write_bytes(content)
                    
                    updated_files.append(member)
            
            return True, updated_files
        except Exception as e:
            logger.error(f"应用更新失败: {e}")
            return False, []

    def reload_modules(self, updated_files: list[str]) -> list[str]:
        """热更新模块"""
        reloaded = []
        
        for file_path in updated_files:
            if not file_path.endswith('.py') or not file_path.startswith('src/'):
                continue
            
            module_name = file_path.replace('src/', '').replace('.py', '').replace('/', '.')
            
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    reloaded.append(module_name)
                    logger.info(f"已重载模块: {module_name}")
                except Exception as e:
                    logger.warning(f"重载模块失败 {module_name}: {e}")
        
        self._load_version()
        return reloaded

    async def rollback(self) -> bool:
        """回滚到上一版本"""
        if not self.backup_path.exists():
            return False

        backups = sorted(self.backup_path.iterdir(), key=lambda x: x.name, reverse=True)
        if not backups:
            return False

        latest_backup = backups[0]
        try:
            src_backup = latest_backup / "src"
            if src_backup.exists():
                src_current = self.base_path / "src"
                if src_current.exists():
                    shutil.rmtree(src_current)
                shutil.copytree(src_backup, src_current)
            
            pyproject_backup = latest_backup / "pyproject.toml"
            if pyproject_backup.exists():
                shutil.copy2(pyproject_backup, self.base_path / "pyproject.toml")
            
            self._load_version()
            logger.info(f"已回滚到: {latest_backup}")
            return True
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False

    def get_latest_backup(self) -> Optional[dict[str, Any]]:
        """获取最新备份信息"""
        if not self.backup_path.exists():
            return None

        backups = sorted(self.backup_path.iterdir(), key=lambda x: x.name, reverse=True)
        if not backups:
            return None

        latest = backups[0]
        stat = latest.stat()
        return {
            "path": str(latest),
            "name": latest.name,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "size": stat.st_size
        }


@router.post("/upload")
async def upload_update(file: UploadFile = File(...)) -> dict[str, Any]:
    """上传并应用更新"""
    if _manager is None:
        raise HTTPException(status_code=503, detail="热更新管理器未初始化")

    if _manager.update_status["updating"]:
        raise HTTPException(status_code=409, detail="正在更新中，请稍候")

    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持zip文件")

    _manager.update_status = {
        "updating": True,
        "progress": 0,
        "message": "开始处理更新包",
        "last_update": datetime.now().isoformat(),
        "error": None
    }

    try:
        if not _manager.temp_path.exists():
            _manager.temp_path.mkdir(parents=True, exist_ok=True)

        temp_file = _manager.temp_path / file.filename
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        _manager.update_status["progress"] = 10
        _manager.update_status["message"] = "验证更新包"

        valid, message = _manager.validate_package(temp_file)
        if not valid:
            raise HTTPException(status_code=400, detail=message)

        _manager.update_status["progress"] = 20
        _manager.update_status["message"] = "备份当前版本"

        backup_path = await _manager.backup_current()
        if not backup_path:
            raise HTTPException(status_code=500, detail="备份失败")

        _manager.update_status["progress"] = 40
        _manager.update_status["message"] = "应用更新"

        success, updated_files = await _manager.apply_update(temp_file)
        if not success:
            await _manager.rollback()
            raise HTTPException(status_code=500, detail="应用更新失败")

        _manager.update_status["progress"] = 70
        _manager.update_status["message"] = "热更新模块"

        reloaded = _manager.reload_modules(updated_files)

        _manager.update_status["progress"] = 90
        _manager.update_status["message"] = "清理临时文件"

        temp_file.unlink(missing_ok=True)

        _manager.update_status = {
            "updating": False,
            "progress": 100,
            "message": "更新完成",
            "last_update": datetime.now().isoformat(),
            "error": None
        }

        return {
            "success": True,
            "message": "更新成功，无需重启",
            "current_version": _manager.current_version,
            "updated_files": len(updated_files),
            "reloaded_modules": reloaded
        }

    except HTTPException:
        raise
    except Exception as e:
        _manager.update_status = {
            "updating": False,
            "progress": 0,
            "message": "更新失败",
            "last_update": datetime.now().isoformat(),
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/status")
async def get_update_status() -> dict[str, Any]:
    """获取更新状态"""
    if _manager is None:
        return {"initialized": False}
    
    return {
        "initialized": True,
        **_manager.update_status,
        "current_version": _manager.current_version
    }


@router.post("/rollback")
async def rollback_update() -> dict[str, Any]:
    """回滚到上一版本"""
    if _manager is None:
        raise HTTPException(status_code=503, detail="热更新管理器未初始化")

    success = await _manager.rollback()
    if success:
        return {
            "success": True,
            "message": "回滚成功",
            "current_version": _manager.current_version
        }
    else:
        raise HTTPException(status_code=500, detail="回滚失败")


@router.get("/version")
async def get_version() -> dict[str, str]:
    """获取当前版本信息"""
    if _manager is None:
        return {"version": "unknown"}
    
    return {
        "version": _manager.current_version or "unknown"
    }


@router.get("/backup")
async def get_backup_info() -> dict[str, Any]:
    """获取备份信息"""
    if _manager is None:
        return {"initialized": False}
    
    backup = _manager.get_latest_backup()
    return {
        "initialized": True,
        "latest_backup": backup
    }
