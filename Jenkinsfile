pipeline {
    agent {
        docker {
            image 'python:3.12'
        }
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                url: '${GIT_REPO_URL}'
            }
        }
        stage('Install') {
            steps {
                sh '''
                    pip install -r requirements.txt
                '''
            }
        }
        stage('Test') {
            steps {
                sh '''
                pytest
                --junitxml=report.xml \
                --cov=. \
                --cov-report=xml 
                '''
            }
        }
    }
    post {

        always {
            junit 'report.xml'
        }
    }
}