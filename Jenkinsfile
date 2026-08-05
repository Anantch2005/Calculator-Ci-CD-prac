pipeline {
    agent none

    stages {

        stage('Checkout') {
            agent any

            steps {
                git branch: 'main',
                    url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
            }
        }
        stage('clean workspace') {
            steps {
                cleanWs()
            }
        }
        stage('Test') {
            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                }
            }

            steps {
                sh '''
                pip install -r requirements.txt

                pytest \
                  --junitxml=report.xml \
                  --cov=. \
                  --cov-report=xml
                '''
            }

            post {
                always {
                    junit 'report.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args '-u root:root'
                }
            }

            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner'
                }
            }
        }

        stage('Build Image') {
            agent {
                docker {
                    image 'docker:28-cli'
                    args '''
                    -u root:root
                    -v /var/run/docker.sock:/var/run/docker.sock
                    '''
                }
            }

            steps {
                sh '''
                docker build -t calculator:latest .
                docker images
                echo "Docker image built successfully."
                '''
            }
        }

        stage('Trivy Scan') {
            agent {
                docker {
                    image 'aquasec/trivy:latest'
                    args '''
                    --entrypoint=''
                    -u root:root
                    -v /var/run/docker.sock:/var/run/docker.sock
                    '''
                }
            }

            steps {
                sh '''
                trivy image calculator:latest
                echo "Trivy scan completed successfully."
                '''
            }
        }
    }
}