@Library('Shared') _

pipeline {

    agent none

    parameters {

        // ==========================================
        // AUTOHEAL CONTROL
        // ==========================================

        booleanParam(
            name: 'AUTOHEAL_RETRY',
            defaultValue: false,
            description: 'Build was triggered by AutoHeal.'
        )

        string(
            name: 'AUTOHEAL_ACTION',
            defaultValue: '',
            description: 'Category-specific AutoHeal remediation action.'
        )

        // ==========================================
        // WORKSPACE REMEDIATION
        // ==========================================

        booleanParam(
            name: 'AUTOHEAL_CLEAN_WORKSPACE',
            defaultValue: false,
            description: 'Clean the Jenkins workspace before checkout.'
        )

        booleanParam(
            name: 'AUTOHEAL_FRESH_CHECKOUT',
            defaultValue: false,
            description: 'Perform a fresh Git checkout after workspace cleanup.'
        )

        // ==========================================
        // DEPENDENCY REMEDIATION
        // ==========================================

        booleanParam(
            name: 'AUTOHEAL_CLEAN_DEPENDENCY_ENV',
            defaultValue: false,
            description: 'Reset the Python dependency environment.'
        )

        booleanParam(
            name: 'AUTOHEAL_INSTALL_FROM_LOCKFILE',
            defaultValue: false,
            description: 'Install dependencies from the repository dependency definition.'
        )

        // ==========================================
        // DOCKER REMEDIATION
        // ==========================================

        booleanParam(
            name: 'AUTOHEAL_DOCKER_NO_CACHE',
            defaultValue: false,
            description: 'Build Docker image without using the build cache.'
        )

        // ==========================================
        // NETWORK REMEDIATION
        // ==========================================

        booleanParam(
            name: 'AUTOHEAL_CONNECTIVITY_CHECK',
            defaultValue: false,
            description: 'Check connectivity from the Jenkins agent.'
        )

        string(
            name: 'AUTOHEAL_BACKOFF_SECONDS',
            defaultValue: '10',
            description: 'Wait before retrying after a network failure.'
        )
    }

    environment {

        IMAGE_NAME = "anant2005ch/calculator"

        IMAGE_TAG = "${BUILD_NUMBER}"

        AUTOHEAL_TEST = "true"
    }

    stages {

        // ============================================================
        // NETWORK RECOVERY
        // ============================================================

        stage('AutoHeal Network Recovery') {

            when {
                expression {
                    return params.AUTOHEAL_CONNECTIVITY_CHECK
                }
            }

            agent any

            steps {

                script {

                    echo "AutoHeal action: ${params.AUTOHEAL_ACTION}"

                    echo "Checking network connectivity from Jenkins agent..."

                    sh '''
                        set -eu

                        echo "Checking DNS resolution..."

                        getent hosts registry-1.docker.io

                        echo "Checking Docker Hub registry..."

                        HTTP_CODE=$(curl \
                            --silent \
                            --show-error \
                            --output /dev/null \
                            --write-out "%{http_code}" \
                            --max-time 10 \
                            https://registry-1.docker.io/v2/)

                        echo "Registry HTTP status: ${HTTP_CODE}"

                        case "${HTTP_CODE}" in
                            200|401|403)
                                echo "Registry reachable."
                                ;;
                            *)
                                echo "Registry connectivity check failed."
                                exit 1
                                ;;
                        esac
                    '''

                    if (params.AUTOHEAL_BACKOFF_SECONDS?.isInteger()) {

                        int seconds =
                            params.AUTOHEAL_BACKOFF_SECONDS.toInteger()

                        if (seconds > 0) {

                            echo(
                                "AutoHeal: backing off for ${seconds} seconds"
                            )

                            sleep(
                                time: seconds,
                                unit: 'SECONDS'
                            )
                        }
                    }
                }
            }
        }

        // ============================================================
        // WORKSPACE RECOVERY
        // ============================================================

        stage('AutoHeal Workspace Recovery') {

            when {
                expression {
                    return params.AUTOHEAL_CLEAN_WORKSPACE
                }
            }

            agent any

            steps {

                script {

                    echo "AutoHeal: cleaning Jenkins workspace..."

                    cleanWs()

                    echo "AutoHeal: workspace cleanup completed."
                }
            }
        }

        // ============================================================
        // CHECKOUT
        // ============================================================

        stage('Checkout') {

            agent any

            steps {

                script {

                    if (params.AUTOHEAL_FRESH_CHECKOUT) {

                        echo "AutoHeal: performing fresh checkout..."
                    }

                    git(
                        branch: 'main',
                        url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
                    )
                }
            }
        }

        // ============================================================
        // DEPENDENCIES + TEST
        // ============================================================

        stage('Test') {

            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                }
            }

            steps {

                script {

                    // ==========================================
                    // TARGETED DEPENDENCY RECOVERY
                    // ==========================================

                    if (params.AUTOHEAL_CLEAN_DEPENDENCY_ENV) {

                        echo(
                            "AutoHeal: resetting dependency environment..."
                        )

                        sh '''
                            set -eu

                            rm -rf .venv

                            python -m venv .venv

                            . .venv/bin/activate

                            python -m pip install --upgrade pip
                        '''
                    }

                    if (params.AUTOHEAL_INSTALL_FROM_LOCKFILE) {

                        echo(
                            "AutoHeal: installing dependencies from repository definition..."
                        )

                        sh '''
                            set -eu

                            if [ -d ".venv" ]; then
                                . .venv/bin/activate
                            fi

                            python -m pip install \
                                --no-cache-dir \
                                -r requirements.txt
                        '''
                    }

                    // ==========================================
                    // NORMAL TEST EXECUTION
                    // ==========================================

                    python_test()
                }
            }

            post {

                always {

                    junit 'report.xml'
                }
            }
        }

        // ============================================================
        // SONARQUBE
        // ============================================================

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

        // ============================================================
        // BUILD DOCKER IMAGE
        // ============================================================

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

                script {

                    // ==========================================
                    // AUTOHEAL DOCKER CLEAN REBUILD
                    // ==========================================

                    if (params.AUTOHEAL_DOCKER_NO_CACHE) {

                        echo(
                            "AutoHeal: Docker failure detected."
                        )

                        echo(
                            "AutoHeal: invalidating Docker build cache..."
                        )

                        sh """
                            docker build \
                                --no-cache \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                .
                        """

                    } else {

                        // Normal pipeline
                        docker_build(
                            image: env.IMAGE_NAME,
                            tag: env.IMAGE_TAG
                        )
                    }
                }
            }
        }

        // ============================================================
        // TRIVY
        // ============================================================

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

        // ============================================================
        // PUSH IMAGE
        // ============================================================

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

    // ================================================================
    // AUTOHEAL WEBHOOK
    // ================================================================

    post {
        failure {
            script {

                echo "Sending Jenkins failure to AutoHeal..."

                docker.image('curlimages/curl:latest').inside(
                    '--add-host=host.docker.internal:host-gateway'
                ) {

                    sh '''
                        set -eu

                        echo "Calling AutoHeal webhook..."

                        HTTP_CODE=$(curl \
                            --silent \
                            --show-error \
                            -o /tmp/autoheal-response.json \
                            -w "%{http_code}" \
                            -X POST \
                            http://host.docker.internal:8000/webhook/jenkins \
                            -H "Content-Type: application/json" \
                            -H "X-AutoHeal-Secret: change-me" \
                            --data-raw "{
                                \\"job_name\\": \\"${JOB_NAME}\\",
                                \\"build_number\\": ${BUILD_NUMBER},
                                \\"build_url\\": \\"${BUILD_URL}\\",
                                \\"status\\": \\"FAILURE\\"
                            }"
                        )

                        echo "AutoHeal HTTP status: ${HTTP_CODE}"

                        if [ -f /tmp/autoheal-response.json ]; then
                            cat /tmp/autoheal-response.json
                        fi
                    '''
                }
            }
        }
    }
}