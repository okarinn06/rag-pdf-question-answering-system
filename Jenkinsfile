pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = "khanhdang21"      
        BACKEND_IMAGE       = "${DOCKERHUB_USERNAME}/rag-pdf-backend"
        FRONTEND_IMAGE      = "${DOCKERHUB_USERNAME}/rag-pdf-frontend"
        IMAGE_TAG           = "${BUILD_NUMBER}"              
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/okarinn06/rag-pdf-question-answering-system.git'
            }
        }

        stage('Build Backend Image') {
            steps {
                sh """
                docker build -f Dockerfile.backend \
                    -t ${BACKEND_IMAGE}:${IMAGE_TAG} \
                    -t ${BACKEND_IMAGE}:latest .
                """
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                }
            }
        }

        stage('Push Images') {
            steps {
                sh """
                docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                docker push ${BACKEND_IMAGE}:latest
                docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                docker push ${FRONTEND_IMAGE}:latest
                """
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([string(
                    credentialsId: 'groq-api-key',
                    variable: 'GROQ_API_KEY'
                )]) {
                    sh """
                    echo "GROQ_API_KEY=\$GROQ_API_KEY" > .env
                    export DOCKERHUB_USERNAME=${DOCKERHUB_USERNAME}
                    export IMAGE_TAG=${IMAGE_TAG}
                    docker compose pull
                    docker compose up -d
                    """
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'  
        }
        success {
            echo "Deploy successfully: Backend http://192.168.116.110:8000/docs | Frontend http://192.168.116.110:8501"
        }
        failure {
            echo "Pipeline fail, check log."
        }
    }
}