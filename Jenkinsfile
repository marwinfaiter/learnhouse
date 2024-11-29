pipeline {
    agent any
    environment {
        NEXT_PUBLIC_LEARNHOUSE_MULTI_ORG = "false"
        NEXT_PUBLIC_LEARNHOUSE_DEFAULT_ORG = "default"
        NEXT_PUBLIC_LEARNHOUSE_API_URL = "https://peertube.buddaphest.se/api/v1/"
        NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL = "https://peertube.buddaphest.se/"
        NEXT_PUBLIC_LEARNHOUSE_DOMAIN = "peertube.buddaphest.se"
        NEXT_PUBLIC_LEARNHOUSE_TOP_DOMAIN = "buddaphest.se"
    }
    stages {
        stage("Clean workspace") {
            steps {
                sh "git clean -xdf"
            }
        }
        stage("Build and push docker image") {
            steps {
                script {
                    docker.withRegistry('https://releases.docker.buddaphest.se', 'nexus') {

                        def customImage = docker.build("marwinfaiter/learnhouse:${env.BUILD_ID}")

                        customImage.push()
                        customImage.push("latest")
                    }
                }
            }
        }
    }
    post {
        always {
            sh "docker system prune -af"
        }
    }
}
