@Library('Shared') _

pipeline {

    agent none

    parameters {
        booleanParam(
            name: 'AUTOHEAL_RETRY',
            defaultValue: false,
            description: 'Set to true when AutoHeal retries a recoverable failure.'
        )
    }

    environment {
        IMAGE_NAME = "anant2005ch/calculator"
        IMAGE_TAG = "${BUILD_NUMBER}"

        // Used by the intentional AutoHeal test.
        AUTOHEAL_TEST = "true"
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
                git(
                    branch: 'main',
                    url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
                )
            }
        }

        stage('Test') {

            agent {
                docker {
                    image 'python:latest'

                    args '--add-host=host.docker.internal:host-gateway -u root:root'
                }
            }

            steps {

                sh '''
                    echo "=========================================="
                    echo "AutoHeal connectivity test"
                    echo "=========================================="

                    curl --fail --silent --show-error \
                        http://host.docker.internal:8000/health

                    echo ""
                    echo "AutoHeal is reachable."
                    echo ""
                '''

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

                    args '--add-host=host.docker.internal:host-gateway -u root:root'
                }
            }

            steps {

                sonarqube_analysis(
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
                        --add-host=host.docker.internal:host-gateway
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
                        --add-host=host.docker.internal:host-gateway
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
                        --add-host=host.docker.internal:host-gateway
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

    post {

        failure {

            script {

                echo "=========================================="
                echo "Jenkins build FAILED"
                echo "Sending incident to AutoHeal"
                echo "=========================================="

                def payload = """
                {
                    "job_name": "${env.JOB_NAME}",
                    "build_number": ${env.BUILD_NUMBER},
                    "build_url": "${env.BUILD_URL}",
                    "status": "FAILURE"
                }
                """

                sh """
                    curl --fail --silent --show-error \
                        -X POST \
                        http://host.docker.internal:8000/webhook/jenkins \
                        -H 'Content-Type: application/json' \
                        -H 'X-AutoHeal-Secret: change-me' \
                        -d '${payload}'
                """
            }
        }
    }
}