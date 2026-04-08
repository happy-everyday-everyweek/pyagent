package com.pyagent.app

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

class ProotManager(private val context: Context) {
    companion object {
        private const val TAG = "ProotManager"
        private const val ROOTFS_DIR = "rootfs"
        private const val PROOT_BINARY = "proot"
    }

    private val rootFsDir: File by lazy {
        File(context.filesDir, ROOTFS_DIR)
    }

    suspend fun initialize(): Boolean = withContext(Dispatchers.IO) {
        try {
            Log.i(TAG, "Initializing PRoot environment...")
            
            if (!rootFsDir.exists()) {
                rootFsDir.mkdirs()
            }

            extractAssets()
            setupSymlinks()
            
            Log.i(TAG, "PRoot environment initialized successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize PRoot", e)
            false
        }
    }

    private suspend fun extractAssets() = withContext(Dispatchers.IO) {
        val assets = context.assets
        val assetList = assets.list("") ?: return@withContext
        
        for (asset in assetList) {
            if (asset.startsWith("rootfs-")) {
                extractAsset(asset, rootFsDir)
            }
        }
    }

    private fun extractAsset(assetName: String, targetDir: File) {
        try {
            val input = context.assets.open(assetName)
            val outputFile = File(targetDir, assetName)
            val output = FileOutputStream(outputFile)
            
            input.copyTo(output)
            input.close()
            output.close()
            
            Log.i(TAG, "Extracted asset: $assetName")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract asset: $assetName", e)
        }
    }

    private fun setupSymlinks() {
        val binDir = File(rootFsDir, "bin")
        if (!binDir.exists()) {
            binDir.mkdirs()
        }
    }

    fun getProotCommand(): List<String> {
        val prootPath = File(context.filesDir, PROOT_BINARY).absolutePath
        return listOf(
            prootPath,
            "-r", rootFsDir.absolutePath,
            "-b", "/dev",
            "-b", "/proc",
            "-b", "/sys",
            "-b", "/data",
            "-w", "/root"
        )
    }

    fun getRootFsPath(): String = rootFsDir.absolutePath

    fun isInitialized(): Boolean = rootFsDir.exists() && 
        File(rootFsDir, "bin").exists()
}
