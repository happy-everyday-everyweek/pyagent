#!/bin/bash

# PyAgent 自动化构建脚本 (Linux 版本)
# 自动完成以下构建任务：
# - 编译Python项目（构建wheel包）
# - 打包APK安装包

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"

# 默认选项
SKIP_WHEEL=false
SKIP_APK=false
NO_CLEAN=false

# 显示帮助信息
show_help() {
    echo "PyAgent 自动化构建脚本 (Linux 版本)"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --skip-wheel    跳过构建wheel包"
    echo "  --skip-apk      跳过构建APK"
    echo "  --no-clean      不清理旧的构建文件"
    echo "  -h, --help      显示帮助信息"
    echo ""
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-wheel)
            SKIP_WHEEL=true
            shift
            ;;
        --skip-apk)
            SKIP_APK=true
            shift
            ;;
        --no-clean)
            NO_CLEAN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 打印头部信息
print_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# 打印成功信息
print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# 打印错误信息
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 打印信息
print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

# 清理构建文件
clean_build() {
    print_header "Cleaning Build Files"
    
    local dirs_to_clean=(
        "$BUILD_DIR"
        "$DIST_DIR"
        "$PROJECT_ROOT/android/app/build"
        "$PROJECT_ROOT/android/.gradle"
        "$PROJECT_ROOT/android/build"
    )
    
    for dir in "${dirs_to_clean[@]}"; do
        if [ -d "$dir" ]; then
            print_info "Removing: $dir"
            rm -rf "$dir"
        fi
    done
    
    print_success "Clean completed"
}

# 构建 wheel 包
build_wheel() {
    print_header "Building Wheel Package"
    
    # 检查是否有 uv 或 pip
    if command -v uv &> /dev/null; then
        print_info "Using uv to build wheel package..."
        uv build --wheel --outdir "$DIST_DIR"
    elif command -v python3 &> /dev/null; then
        print_info "Using python3 to build wheel package..."
        python3 -m build --wheel --outdir "$DIST_DIR"
    else
        print_error "Neither uv nor python3 found"
        exit 1
    fi
    
    # 检查构建是否成功
    local wheel_file=$(ls -t "$DIST_DIR"/*.whl 2>/dev/null | head -1)
    if [ -n "$wheel_file" ]; then
        print_success "Wheel package created: $wheel_file"
    else
        print_error "Wheel build failed"
        exit 1
    fi
}

# 构建 APK
build_apk() {
    print_header "Building APK Package"
    
    local android_dir="$PROJECT_ROOT/android"
    
    if [ ! -d "$android_dir" ]; then
        print_error "Android project not found: $android_dir"
        exit 1
    fi
    
    # 检查是否有 gradlew 或 gradle
    local gradle_cmd
    if [ -f "$android_dir/gradlew" ]; then
        gradle_cmd="$android_dir/gradlew"
        chmod +x "$gradle_cmd"
    elif command -v gradle &> /dev/null; then
        gradle_cmd="gradle"
    else
        print_error "Gradle not found"
        exit 1
    fi
    
    print_info "Running Gradle build..."
    
    cd "$android_dir"
    $gradle_cmd assembleDebug --no-daemon
    
    # 检查 APK 是否生成
    local apk_file="$android_dir/app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$apk_file" ]; then
        print_success "APK created: $apk_file"
    else
        print_error "APK build failed"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
}

# 主函数
main() {
    local start_time=$(date +%s)
    
    print_header "PyAgent Build Script"
    print_info "Project Root: $PROJECT_ROOT"
    print_info "Build Wheel: $([ "$SKIP_WHEEL" = false ] && echo "true" || echo "false")"
    print_info "Build APK: $([ "$SKIP_APK" = false ] && echo "true" || echo "false")"
    print_info "Clean: $([ "$NO_CLEAN" = false ] && echo "true" || echo "false")"
    
    # 清理旧文件
    if [ "$NO_CLEAN" = false ]; then
        clean_build
    fi
    
    # 创建输出目录
    mkdir -p "$DIST_DIR"
    mkdir -p "$BUILD_DIR"
    
    # 构建 wheel
    if [ "$SKIP_WHEEL" = false ]; then
        build_wheel
    fi
    
    # 构建 APK
    if [ "$SKIP_APK" = false ]; then
        build_apk
    fi
    
    # 计算耗时
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    print_header "Build Summary"
    echo "Total Duration: ${minutes}m ${seconds}s"
    echo ""
    echo -e "${CYAN}Output Files:${NC}"
    
    if [ "$SKIP_WHEEL" = false ]; then
        local wheel_file=$(ls -t "$DIST_DIR"/*.whl 2>/dev/null | head -1)
        if [ -n "$wheel_file" ]; then
            echo -e "  Wheel: $wheel_file"
        fi
    fi
    
    if [ "$SKIP_APK" = false ]; then
        local apk_file="$PROJECT_ROOT/android/app/build/outputs/apk/debug/app-debug.apk"
        if [ -f "$apk_file" ]; then
            echo -e "  APK: $apk_file"
        fi
    fi
    
    echo ""
    print_success "Build completed successfully!"
}

# 执行主函数
main
