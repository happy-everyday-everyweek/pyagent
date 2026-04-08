package com.pyagent.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class BackendService : Service() {
    companion object {
        private const val TAG = "BackendService"
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "pyagent_service_channel"
        
        fun startService(context: Context) {
            val intent = Intent(context, BackendService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stopService(context: Context) {
            val intent = Intent(context, BackendService::class.java)
            context.stopService(intent)
        }
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val binder = LocalBinder()
    private lateinit var prootManager: ProotManager
    private lateinit var pythonRuntime: PythonRuntime

    inner class LocalBinder : Binder() {
        fun getService(): BackendService = this@BackendService
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Creating backend service")
        
        prootManager = ProotManager(this)
        pythonRuntime = PythonRuntime(this, prootManager)
        
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "Starting backend service command")
        
        serviceScope.launch {
            initializeAndStart()
        }
        
        return START_STICKY
    }

    private suspend fun initializeAndStart() {
        try {
            if (!pythonRuntime.initialize()) {
                Log.e(TAG, "Failed to initialize Python runtime")
                return
            }
            
            if (!pythonRuntime.startBackend()) {
                Log.e(TAG, "Failed to start backend")
                return
            }
            
            Log.i(TAG, "Backend service fully initialized and running")
        } catch (e: Exception) {
            Log.e(TAG, "Error in service initialization", e)
        }
    }

    override fun onBind(intent: Intent?): IBinder {
        return binder
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.i(TAG, "Destroying backend service")
        
        serviceScope.launch {
            pythonRuntime.stopBackend()
        }
    }

    fun isBackendRunning(): Boolean = pythonRuntime.isBackendRunning()

    fun getBackendUrl(): String = pythonRuntime.getBackendUrl()

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "PyAgent Backend",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "PyAgent backend service is running"
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("PyAgent")
            .setContentText("Backend service is running")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
}
