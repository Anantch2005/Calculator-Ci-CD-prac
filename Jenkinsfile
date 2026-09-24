@Library('Shared') _

pipeline {
    agent none

    options {
        skipDefaultCheckout(true)
    }

    parameters {

        booleanParam(
            name: 'AUTOHEAL_RETRY',
            defaultValue: false,
            description: 'Set by AutoHeal when a recovery retry is requested.'
        )

        choice(
            name: 'AUTOHEAL_ACTION',
            choices: [
                'NONE',
                'RETRY_FLAKY_TEST',
                'CLEAN_WORKSPACE',
                'CLEAN_DEPENDENCY_ENV',
                'INVALIDATE_DOCKER_CACHE',
                'CONNECTIVITY_CHECK_BACKOFF',
                'RETRY_REGISTRY'
            ],
            description: 'Internal AutoHeal remediation action.'
        )

        booleanParam(
            name: 'AUTOHEAL_CLEAN_WORKSPACE',
            defaultValue: false,
            description: 'Clean Jenkins workspace before retry.'
        )

        booleanParam(
            name: 'AUTOHEAL_FRESH_CHECKOUT',
            defaultValue: false,
            description: 'Perform a fresh repository checkout.'
        )

        booleanParam(
            name: 'AUTOHEAL_CLEAN_DEPENDENCY_ENV',
            defaultValue: false,
            description: 'Force a clean dependency environment.'
        )

        booleanParam(
            name: 'AUTOHEAL_INSTALL_FROM_LOCKFILE',
            defaultValue: false,
            description: 'Install dependencies from the lockfile.'
        )

        booleanParam(
            name: 'AUTOHEAL_DOCKER_NO_CACHE',
            defaultValue: false,
            description: 'Build Docker image without cache.'
        )

        booleanParam(
            name: 'AUTOHEAL_CONNECTIVITY_CHECK',
            defaultValue: false,
            description: 'Run connectivity checks before retry.'
        )

        string(
            name: 'AUTOHEAL_BACKOFF_SECONDS',
            defaultValue: '0',
            description: 'Backoff before retry in seconds.'
        )
    }

    environment {
        IMAGE_NAME = 'anant2005/calculator'
        IMAGE_TAG  = "${BUILD_NUMBER}"

        // Used by the intentional AutoHeal test in test_calculator.py
        AUTOHEAL_TEST = 'true'
    }

    stages {

        // ============================================================
        // AUTOHEAL WORKSPACE RECOVERY
        // ============================================================

        stage('AutoHeal - Workspace Recovery') {

            when {
                beforeAgent true

                allOf {
                    expression {
                        params.AUTOHEAL_RETRY
                    }

                    expression {
                        params.AUTOHEAL_ACTION == 'CLEAN_WORKSPACE' ||
                        params.AUTOHEAL_CLEAN_WORKSPACE
                    }
                }
            }

            agent any

            steps {
                echo 'AutoHeal: cleaning Jenkins workspace...'

                cleanWs(
                    deleteDirs: true,
                    disableDeferredWipeout: true,
                    notFailBuild: false
                )

                echo 'AutoHeal: workspace cleanup completed.'
            }
        }

        // ============================================================
        // CHECKOUT
        // ============================================================

        stage('Checkout') {

            agent any

            steps {
                echo 'Checking out source code...'

                checkout scm

                echo 'Checkout completed.'
            }
        }

        // ============================================================
        // AUTOHEAL DEPENDENCY RECOVERY
        // ============================================================

        stage('AutoHeal - Dependency Recovery') {

            when {
                beforeAgent true

                allOf {
                    expression {
                        params.AUTOHEAL_RETRY
                    }

                    expression {
                        params.AUTOHEAL_ACTION == 'CLEAN_DEPENDENCY_ENV' ||
                        params.AUTOHEAL_CLEAN_DEPENDENCY_ENV
                    }
                }
            }

            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                }
            }

            steps {
                echo 'AutoHeal: preparing clean dependency environment...'

                sh '''
                    set -eux

                    rm -rf .venv

                    python -m venv .venv

                    . .venv/bin/activate

                    python -m pip install --upgrade pip

                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''

                echo 'AutoHeal: dependency recovery preparation completed.'
            }
        }

        // ============================================================
        // AUTOHEAL NETWORK RECOVERY
        // ============================================================

        stage('AutoHeal - Network Recovery') {

            when {
                beforeAgent true

                allOf {
                    expression {
                        params.AUTOHEAL_RETRY
                    }

                    expression {
                        params.AUTOHEAL_ACTION == 'CONNECTIVITY_CHECK_BACKOFF' ||
                        params.AUTOHEAL_CONNECTIVITY_CHECK
                    }
                }
            }

            agent any

            steps {
                script {

                    int backoff = 0

                    try {
                        backoff = params.AUTOHEAL_BACKOFF_SECONDS.toInteger()
                    } catch (Exception ignored) {
                        backoff = 0
                    }

                    if (backoff > 0) {
                        echo "AutoHeal: waiting ${backoff} seconds before retry..."

                        sleep(
                            time: backoff,
                            unit: 'SECONDS'
                        )
                    }

                    echo 'AutoHeal: checking network connectivity...'

                    sh '''
                        set +e

                        echo "Checking DNS..."
                        getent hosts github.com || true

                        echo "Checking HTTPS connectivity..."
                        curl \
                            --silent \
                            --show-error \
                            --max-time 10 \
                            https://github.com \
                            -o /dev/null

                        STATUS=$?

                        echo "Connectivity check exit code: ${STATUS}"

                        exit 0
                    '''
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

                echo 'Running Python tests...'

                script {
                    python_test(
                        requirements: 'requirements.txt',
                        testCommand: 'pytest',
                        junitReport: 'report.xml',
                        coverage: true,
                        coverageFile: 'coverage.xml'
                    )
                }
            }

            post {

                always {

                    junit(
                        testResults: 'report.xml',
                        allowEmptyResults: true
                    )

                    archiveArtifacts(
                        artifacts: 'coverage.xml',
                        allowEmptyArchive: true
                    )
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

                script {

                    sonarqube_analysis(
                        server: 'SonarQube',
                        scanner: 'sonar-scanner'
                    )
                }
            }
        }

        // ============================================================
        // DOCKER BUILD
        // ============================================================

        stage('Docker Build') {

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

                    if (params.AUTOHEAL_DOCKER_NO_CACHE) {

                        echo 'AutoHeal: Docker no-cache recovery requested.'

                        sh """
                            docker build \
                                --no-cache \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                .
                        """

                    } else {

                        docker_build(
                            image: IMAGE_NAME,
                            tag: IMAGE_TAG
                        )
                    }
                }
            }
        }

        // ============================================================
        // TRIVY SECURITY SCAN
        // ============================================================

        stage('Trivy Security Scan') {

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

                script {

                    trivy_scan(
                        image: IMAGE_NAME,
                        tag: IMAGE_TAG,
                        severity: 'CRITICAL,HIGH',
                        exitCode: '0'
                    )
                }
            }
        }

        // ============================================================
        // DOCKER PUSH
        // ============================================================

        stage('Docker Push') {

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

                    docker_push(
                        image: IMAGE_NAME,
                        tag: IMAGE_TAG,
                        credentialsId: 'dockerhub'
                    )
                }
            }
        }
    }

    // ================================================================
    // AUTOHEAL FAILURE WEBHOOK
    // ================================================================

    post {

        failure {

            node('built-in') {

                script {

                    sh(
                        script: '''
                            set +e

                            HTTP_CODE=$(curl \
                                --silent \
                                --show-error \
                                --output /tmp/autoheal-response.json \
                                --write-out "%{http_code}" \
                                --max-time 15 \
                                -X POST \
                                http://127.0.0.1:8000/webhook/jenkins \
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
                                echo "AutoHeal response:"
                                cat /tmp/autoheal-response.json
                            fi

                            if [ "${HTTP_CODE}" = "000" ]; then
                                echo "WARNING: AutoHeal webhook could not be reached."

                            elif [ "${HTTP_CODE}" != "200" ]; then
                                echo "WARNING: AutoHeal returned HTTP ${HTTP_CODE}"

                            else
                                echo "AutoHeal successfully received the failure."
                            fi

                            exit 0
                        ''',
                        label: 'Notify AutoHeal'
                    )
                }
            }
        }
    }
}