pipeline {
    agent any

    parameters {
        string(name: 'BRANCH_NAME', defaultValue: 'main', description: 'Git branch to build and deploy')
        string(name: 'BROKER_API_KEY', defaultValue: '', description: 'Broker API Key')
        password(name: 'BROKER_API_SECRET', defaultValue: '', description: 'Broker API Secret')
        string(name: 'APP_KEY', defaultValue: '', description: 'App Key (Leave empty to auto-generate)')
        string(name: 'API_KEY_PEPPER', defaultValue: '', description: 'API Key Pepper (Leave empty to auto-generate)')
        string(name: 'HOST_SERVER', defaultValue: 'http://127.0.0.1:5000', description: 'Host Server URL')
        string(name: 'FLASK_PORT', defaultValue: '5000', description: 'Flask Port')
        choice(name: 'LOG_LEVEL', choices: ['INFO', 'DEBUG', 'WARNING', 'ERROR'], description: 'Log Level')
    }

    environment {
        APP_NAME = 'openalgo-web'
        REPO_URL = 'https://github.com/marketcalls/openalgo.git'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "Checking out branch: ${params.BRANCH_NAME}"
                    // Clean workspace to ensure fresh checkout
                    cleanWs()
                    
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "*/${params.BRANCH_NAME}"]],
                        userRemoteConfigs: [[url: "${env.REPO_URL}"]]
                    ])
                }
            }
        }

        stage('Check Ports') {
            steps {
                script {
                    echo "Checking for available ports..."
                    def ports = sh(script: "python3 find_ports.py", returnStdout: true).trim().split(',')
                    env.FREE_FLASK_PORT = ports[0]
                    env.FREE_WS_PORT = ports[1]
                    env.APP_NAME = "openalgo-${env.FREE_FLASK_PORT}"
                    env.FLASK_PORT = env.FREE_FLASK_PORT
                    env.HOST_SERVER = "http://127.0.0.1:${env.FREE_FLASK_PORT}"
                    
                    echo "Allocated Ports - Web: ${env.FREE_FLASK_PORT}, WebSocket: ${env.FREE_WS_PORT}"
                }
            }
        }

        stage('Configure Environment') {
            steps {
                script {
                    echo "Configuring .env file from .sample.env"
                    sh 'cp .sample.env .env'
                    
                    // Run the Python script to update .env
                    sh 'python3 update_env.py'
                    
                    // Update WebSocket ports in .env
                    sh "sed -i \"s/^WEBSOCKET_PORT=.*/WEBSOCKET_PORT='${env.FREE_WS_PORT}'/\" .env"
                    sh "sed -i \"s|^WEBSOCKET_URL=.*|WEBSOCKET_URL='ws://127.0.0.1:${env.FREE_WS_PORT}'|\" .env"
                }
            }
        }

        stage('Build and Deploy') {
            steps {
                script {
                    echo "Building OpenAlgo from branch: ${params.BRANCH_NAME}"
                    
                    // Build Docker image
                    sh "docker build -t openalgo:${params.BRANCH_NAME} ."
                    
                    // Stop and remove existing container if running
                    sh "docker stop ${env.APP_NAME} || true"
                    sh "docker rm ${env.APP_NAME} || true"
                    
                    // Run new container
                    // Maps dynamic ports
                    sh "docker run -d --name ${env.APP_NAME} -p ${env.FREE_FLASK_PORT}:${env.FREE_FLASK_PORT} -p ${env.FREE_WS_PORT}:${env.FREE_WS_PORT} --restart unless-stopped openalgo:${params.BRANCH_NAME}"
                }
            }
        }
    }
}
