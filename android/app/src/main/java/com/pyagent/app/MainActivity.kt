package com.pyagent.app

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.pyagent.app.api.ApiClient
import com.pyagent.app.api.Task
import com.pyagent.app.ui.theme.PyAgentTheme
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class MainActivity : ComponentActivity() {
    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PyAgentTheme {
                val navController = rememberNavController()
                var tasks by remember { mutableStateOf<List<Task>>(emptyList()) }
                
                // 加载任务数据
                fun loadTasks() {
                    ApiClient.apiService.getTasks().enqueue(object : Callback<com.pyagent.app.api.TaskResponse> {
                        override fun onResponse(
                            call: Call<com.pyagent.app.api.TaskResponse>,
                            response: Response<com.pyagent.app.api.TaskResponse>
                        ) {
                            if (response.isSuccessful) {
                                val taskResponse = response.body()
                                val allTasks = mutableListOf<Task>()
                                taskResponse?.tasks?.let { allTasks.addAll(it) }
                                taskResponse?.running?.let { allTasks.addAll(it) }
                                taskResponse?.completed?.let { allTasks.addAll(it) }
                                taskResponse?.failed?.let { allTasks.addAll(it) }
                                tasks = allTasks
                            }
                        }

                        override fun onFailure(call: Call<com.pyagent.app.api.TaskResponse>, t: Throwable) {
                            Log.e("MainActivity", "Failed to load tasks", t)
                        }
                    })
                }
                
                // 初始加载任务
                loadTasks()
                
                Scaffold(modifier = Modifier.fillMaxSize()) {
                    NavHost(
                        navController = navController,
                        startDestination = "chat",
                        modifier = Modifier.padding(it)
                    ) {
                        composable("chat") {
                            ChatScreen(navController = navController)
                        }
                        composable("tasks") {
                            TasksScreen(
                                navController = navController,
                                tasks = tasks,
                                onRefresh = { loadTasks() }
                            )
                        }
                        composable("config") {
                            ConfigScreen(navController = navController)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ChatScreen(navController: androidx.navigation.NavHostController) {
    Text(
        text = "Chat Screen",
        modifier = Modifier.padding(16.dp)
    )
}

@Composable
fun TasksScreen(
    navController: androidx.navigation.NavHostController,
    tasks: List<Task>,
    onRefresh: () -> Unit
) {
    Text(
        text = "Tasks Screen - ${tasks.size} tasks",
        modifier = Modifier.padding(16.dp)
    )
}

@Composable
fun ConfigScreen(navController: androidx.navigation.NavHostController) {
    Text(
        text = "Config Screen",
        modifier = Modifier.padding(16.dp)
    )
}

@Preview(showBackground = true)
@Composable
fun MainScreenPreview() {
    PyAgentTheme {
        Scaffold {
            Text(
                text = "PyAgent - Python Agent",
                modifier = Modifier.padding(it)
            )
        }
    }
}
