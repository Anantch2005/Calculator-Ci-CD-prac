@Library('Shared') _

pipeline {
    agent none

    parameters {
        booleanParam(
            name: 'AUTOHEAL_RETRY',
            defaultValue: false,
            description: 'Used by AutoHeal when retrying a recoverable failure.'
        )
    }

    environment {
        IMAGE_NAME = "anant2005ch/calculator"
        IMAGE_TAG = "${BUILD_NUMBER}"
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

    post {
        failure {
            script {

                echo "Sending Jenkins failure to AutoHeal..."

                docker.image('curlimages/curl:latest').inside(
                    '--add-host=host.docker.internal:host-gateway'
                ) {

                    sh """
                        HTTP_CODE=\$(curl --silent --show-error \
                            -o /tmp/autoheal-response.json \
                            -w "%{http_code}" \
                            -X POST \
                            http://host.docker.internal:8000/webhook/jenkins \
                            -H 'Content-Type: application/json' \
                            -H 'X-AutoHeal-Secret: change-me' \
                            --data-raw '{
                                "job_name": "${env.JOB_NAME}",
                                "build_number": ${env.BUILD_NUMBER},
                                "build_url": "${env.BUILD_URL}",
                                "status": "FAILURE"
                            }')

                        echo "AutoHeal HTTP status: \${HTTP_CODE}"

                        if [ -f /tmp/autoheal-response.json ]; then
                            cat /tmp/autoheal-response.json
                        fi
                    """
                }
            }
        }
    }
}