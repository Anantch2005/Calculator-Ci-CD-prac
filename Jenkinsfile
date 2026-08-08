@Library('Shared') _

pipeline {
    agent none

    environment {
        IMAGE_NAME = "anant2005ch/calculator"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Clean Workspace') {
            agent any
            steps {
                cleanWs()
            }
        }

        stage('Checkout') {
            agent any
            steps {
                git branch: 'main',
                    url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:latest'
                    args '-u root:root'
                }
            }
            steps {
                python_test()
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
                sonarqube_analysis (
                    server: 'SonarQube',
                    scanner: 'sonar-scanner'
                )   
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
                docker_build(
                    image: env.IMAGE_NAME,
                    tag: env.IMAGE_TAG
                )
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
                trivy_scan(
                    image: env.IMAGE_NAME,
                    tag: env.IMAGE_TAG
                )
            }
        }

        stage('Push Image') {
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
                docker_push(
                    image: env.IMAGE_NAME,
                    tag: env.IMAGE_TAG,
                    credentialsId: 'dockerhub'
                )
            }
        }
    }
}