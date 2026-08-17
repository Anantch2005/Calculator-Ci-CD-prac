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

        // Important:
        // The normal calculator flaky test must stay disabled
        // for this AI-specific validation.
        AUTOHEAL_TEST = "false"
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

        /*
         * PHASE 5 — CONTROLLED AI VALIDATION
         *
         * The normal test stage succeeds.
         *
         * This stage intentionally creates a failure that:
         *
         * 1. Does NOT contain AUTOHEAL_FLAKY_TEST
         * 2. Does NOT use the obvious rule signatures
         * 3. Contains enough evidence for Ollama to diagnose
         *
         * Normal build:
         *
         *   AUTOHEAL_RETRY=false
         *          ↓
         *   AI Test Failure
         *          ↓
         *       FAILURE
         *
         * AutoHeal retry:
         *
         *   AUTOHEAL_RETRY=true
         *          ↓
         *   stage is skipped
         *          ↓
         *       pipeline succeeds
         */
        stage('AI Test Failure') {

            agent any

            when {
                expression {
                    return !params.AUTOHEAL_RETRY
                }
            }

            steps {
                sh '''
                    echo "CI DIAGNOSTIC FAILURE"
                    echo "component: artifact-consumer"
                    echo "operation: fetch-release-metadata"
                    echo "upstream service response code: HTTP 503"
                    echo "upstream service status: temporarily unavailable"
                    echo "health endpoint responded successfully before failure"
                    echo "release metadata operation aborted"
                    echo "attempt-count: 3"
                    echo "final-state: unsuccessful"
                    echo "diagnostic marker: AI_NETWORK_CASE_7419"
                    exit 1
                '''
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
                        curl --fail --silent --show-error \
                            -X POST \
                            http://host.docker.internal:8000/webhook/jenkins \
                            -H 'Content-Type: application/json' \
                            -H 'X-AutoHeal-Secret: change-me' \
                            --data-raw '{
                                "job_name": "${env.JOB_NAME}",
                                "build_number": ${env.BUILD_NUMBER},
                                "build_url": "${env.BUILD_URL}",
                                "status": "FAILURE"
                            }'
                    """
                }
            }
        }
    }
}