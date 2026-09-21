@Library('Shared') _

pipeline {

    agent none

    options {
        /*
         * We perform checkout explicitly in the Checkout stage.
         * Without this, Jenkins automatically performs a checkout
         * whenever a stage gets its own agent.
         */
        skipDefaultCheckout(true)
    }

    parameters {

        // ============================================================
        // AUTOHEAL
        // ============================================================

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

        // ============================================================
        // WORKSPACE RECOVERY
        // ============================================================

        booleanParam(
            name: 'AUTOHEAL_CLEAN_WORKSPACE',
            defaultValue: false,
            description: 'Clean Jenkins workspace before checkout.'
        )

        booleanParam(
            name: 'AUTOHEAL_FRESH_CHECKOUT',
            defaultValue: false,
            description: 'Perform a fresh checkout.'
        )

        // ============================================================
        // DEPENDENCY RECOVERY
        // ============================================================

        booleanParam(
            name: 'AUTOHEAL_CLEAN_DEPENDENCY_ENV',
            defaultValue: false,
            description: 'Reset dependency environment/cache.'
        )

        booleanParam(
            name: 'AUTOHEAL_INSTALL_FROM_LOCKFILE',
            defaultValue: false,
            description: 'Install dependencies from the repository definition.'
        )

        // ============================================================
        // DOCKER RECOVERY
        // ============================================================

        booleanParam(
            name: 'AUTOHEAL_DOCKER_NO_CACHE',
            defaultValue: false,
            description: 'Build Docker image without Docker build cache.'
        )

        // ============================================================
        // NETWORK RECOVERY
        // ============================================================

        booleanParam(
            name: 'AUTOHEAL_CONNECTIVITY_CHECK',
            defaultValue: false,
            description: 'Run connectivity checks from the Jenkins agent.'
        )

        string(
            name: 'AUTOHEAL_BACKOFF_SECONDS',
            defaultValue: '10',
            description: 'Backoff before retry after network failure.'
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

                    echo "========================================"
                    echo "AutoHeal Network Recovery"
                    echo "========================================"

                    echo "Action: ${params.AUTOHEAL_ACTION}"

                    echo "Checking DNS resolution..."

                    sh '''
                        set -eu

                        getent hosts registry-1.docker.io
                    '''

                    echo "Checking Docker Hub registry..."

                    sh '''
                        set -eu

                        HTTP_CODE=$(curl \
                            --silent \
                            --show-error \
                            --output /dev/null \
                            --write-out "%{http_code}" \
                            --max-time 10 \
                            https://registry-1.docker.io/v2/)

                        echo "Docker registry HTTP status: ${HTTP_CODE}"

                        case "${HTTP_CODE}" in
                            200|401|403)
                                echo "Docker registry is reachable."
                                ;;
                            *)
                                echo "Docker registry connectivity check failed."
                                exit 1
                                ;;
                        esac
                    '''

                    if (
                        params.AUTOHEAL_BACKOFF_SECONDS?.isInteger()
                    ) {

                        int seconds =
                            params.AUTOHEAL_BACKOFF_SECONDS.toInteger()

                        if (seconds > 0) {

                            echo(
                                "AutoHeal: backing off for ${seconds} seconds..."
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

                    echo "========================================"
                    echo "AutoHeal Workspace Recovery"
                    echo "========================================"

                    echo "Cleaning Jenkins workspace..."

                    cleanWs()

                    echo "Workspace cleanup completed."

                    if (params.AUTOHEAL_FRESH_CHECKOUT) {

                        echo "Fresh checkout requested by AutoHeal."
                    }
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

                        echo "AutoHeal: performing fresh checkout."
                    }

                    git(
                        branch: 'main',
                        url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
                    )
                }
            }
        }

        // ============================================================
        // TEST
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

                    // ====================================================
                    // DEPENDENCY RECOVERY
                    // ====================================================

                    if (params.AUTOHEAL_CLEAN_DEPENDENCY_ENV) {

                        echo "========================================"
                        echo "AutoHeal Dependency Recovery"
                        echo "========================================"

                        echo "Cleaning Python virtual environment..."

                        sh '''
                            set -eu

                            rm -rf .venv

                            python -m venv .venv

                            echo "Virtual environment recreated."
                        '''

                    }

                    if (params.AUTOHEAL_INSTALL_FROM_LOCKFILE) {

                        echo "AutoHeal: installing dependencies from repository definition."

                        sh '''
                            set -eu

                            . .venv/bin/activate

                            python -m pip install \
                                --no-cache-dir \
                                -r requirements.txt
                        '''
                    }

                    // ====================================================
                    // NORMAL SHARED-LIBRARY TEST
                    // ====================================================

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
        // DOCKER BUILD
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

                    // ====================================================
                    // AUTOHEAL DOCKER RECOVERY
                    // ====================================================

                    if (params.AUTOHEAL_DOCKER_NO_CACHE) {

                        echo "========================================"
                        echo "AutoHeal Docker Recovery"
                        echo "========================================"

                        echo "Invalidating Docker build cache..."

                        sh """
                            docker build \
                                --no-cache \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                .
                        """

                    } else {

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
    // AUTOHEAL FAILURE WEBHOOK
    // ================================================================

    post {

        failure {

            script {

                echo "========================================"
                echo "Sending failure to AutoHeal"
                echo "========================================"

                /*
                 * IMPORTANT:
                 *
                 * Jenkins is running directly on the host.
                 *
                 * AutoHeal is exposed only on:
                 *
                 * 127.0.0.1:8000
                 *
                 * Therefore Jenkins should call AutoHeal directly
                 * through localhost instead of launching another
                 * Docker container and using host.docker.internal.
                 */

                sh """
                    set +e

                    HTTP_CODE=\\$(curl \
                        --silent \
                        --show-error \
                        --output /tmp/autoheal-response.json \
                        --write-out "%{http_code}" \
                        --max-time 15 \
                        -X POST \
                        http://127.0.0.1:8000/webhook/jenkins \
                        -H 'Content-Type: application/json' \
                        -H 'X-AutoHeal-Secret: change-me' \
                        --data-raw '{
                            "job_name": "${env.JOB_NAME}",
                            "build_number": ${env.BUILD_NUMBER},
                            "build_url": "${env.BUILD_URL}",
                            "status": "FAILURE"
                        }')

                    echo "AutoHeal HTTP status: \\${HTTP_CODE}"

                    if [ -f /tmp/autoheal-response.json ]; then
                        echo "AutoHeal response:"
                        cat /tmp/autoheal-response.json
                    fi

                    if [ "\\${HTTP_CODE}" = "000" ]; then
                        echo "WARNING: AutoHeal webhook could not be reached."
                    fi

                    if [ "\\${HTTP_CODE}" != "200" ]; then
                        echo "WARNING: AutoHeal returned HTTP status \\${HTTP_CODE}"
                    fi

                    exit 0
                """
            }
        }
    }
}