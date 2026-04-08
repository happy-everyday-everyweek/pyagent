package com.pyagent.app

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

class PythonRuntime(
    private val context: Context,
    private val prootManager: ProotManager
) {
    companion object {
        private const val TAG = "PythonRuntime"
        private const val PYTHON_BIN = "python3"
        private const val PIP_BIN = "pip3"
        private const val APP_DIR = "/root/pyagent"
    }

    private var process: Process? = null
    private var isRunning = false

    suspend fun initialize(): Boolean = withContext(Dispatchers.IO) {
        try {
            Log.i(TAG, "Initializing Python runtime...")
            
            if (!prootManager.isInitialized()) {
                if (!prootManager.initialize()) {
                    Log.e(TAG, "Failed to initialize PRoot")
                    return@withContext false
                }
            }

            extractPythonAssets()
            installDependencies()
            
            Log.i(TAG, "Python runtime initialized successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize Python runtime", e)
            false
        }
    }

    private suspend fun extractPythonAssets() = withContext(Dispatchers.IO) {
        val appDir = File(prootManager.getRootFsPath(), APP_DIR.drop(1))
        if (!appDir.exists()) {
            appDir.mkdirs()
        }

        try {
            val pyagentSrc = File(context.filesDir.parentFile, "src")
            if (pyagentSrc.exists()) {
                pyagentSrc.copyRecursively(File(appDir, "src"), overwrite = true)
            }

            val pyprojectToml = File(context.filesDir.parentFile, "pyproject.toml")
            if (pyprojectToml.exists()) {
                pyprojectToml.copyTo(File(appDir, "pyproject.toml"), overwrite = true)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract Python assets", e)
        }
    }

    private suspend fun installDependencies() = withContext(Dispatchers.IO) {
        try {
            Log.i(TAG, "Installing Python dependencies...")
            
            val cmd = prootManager.getProotCommand() + listOf(
                PIP_BIN, "install", "-e", APP_DIR
            )

            val processBuilder = ProcessBuilder(cmd)
            processBuilder.directory(File(prootManager.getRootFsPath()))
            processBuilder.redirectErrorStream(true)
            
            val proc = processBuilder.start()
            val exitCode = proc.waitFor()
            
            if (exitCode == 0) {
                Log.i(TAG, "Dependencies installed successfully")
            } else {
                Log.e(TAG, "Failed to install dependencies, exit code: $exitCode")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error installing dependencies", e)
        }
    }

    suspend fun startBackend(): Boolean = withContext(Dispatchers.IO) {
        try {
            if (isRunning) {
                Log.w(TAG, "Backend already running")
                return@withContext true
            }

            Log.i(TAG, "Starting PyAgent backend...")
            
            val cmd = prootManager.getProotCommand() + listOf(
                PYTHON_BIN, "-m", "uvicorn", "src.web.app:app",
                "--host", "127.0.0.1",
                "--port", "8000"
            )

            val processBuilder = ProcessBuilder(cmd)
            processBuilder.directory(File(prootManager.getRootFsPath(), APP_DIR.drop(1)))
            processBuilder.redirectErrorStream(true)
            
            process = processBuilder.start()
            isRunning = true

            Log.i(TAG, "PyAgent backend started successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start backend", e)
            isRunning = false
            false
        }
    }

    suspend fun stopBackend() = withContext(Dispatchers.IO) {
        try {
            process?.destroy()
            process?.waitFor()
            process = null
            isRunning = false
            Log.i(TAG, "PyAgent backend stopped")
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping backend", e)
        }
    }

    fun isBackendRunning(): Boolean = isRunning

    fun getBackendUrl(): String = "http://127.0.0.1:8000"
}
