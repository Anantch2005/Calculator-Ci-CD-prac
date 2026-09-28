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
                'CONNECTIVITY_CHECK_BACKOFF_AND_RETRY',
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

        choice(
            name: 'AUTOHEAL_TEST_FAILURE',
            choices: [
                'NONE',
                'FLAKY_TEST',
                'WORKSPACE_FAILURE',
                'DEPENDENCY_FAILURE',
                'NETWORK_FAILURE',
                'DOCKER_FAILURE',
                'REGISTRY_FAILURE'
            ],
            description: 'Temporary AutoHeal end-to-end test selector. Leave NONE for normal builds.'
        )
    }

    environment {
        IMAGE_NAME = 'anant2005ch/calculator'
        IMAGE_TAG = "${BUILD_NUMBER}"
        AUTOHEAL_TEST = 'true'
    }

    stages {

        /*
         * ============================================================
         * CHECKOUT
         * ============================================================
         */
        stage('Checkout') {

            agent any

            steps {

                script {

                    /*
                     * Debug AutoHeal parameters.
                     * Useful for verifying exactly what the retry
                     * request passed into Jenkins.
                     */
                    if (params.AUTOHEAL_RETRY) {

                        echo '========== AutoHeal Retry Parameters =========='
                        echo "AUTOHEAL_RETRY: ${params.AUTOHEAL_RETRY}"
                        echo "AUTOHEAL_ACTION: ${params.AUTOHEAL_ACTION}"
                        echo "AUTOHEAL_CLEAN_WORKSPACE: ${params.AUTOHEAL_CLEAN_WORKSPACE}"
                        echo "AUTOHEAL_FRESH_CHECKOUT: ${params.AUTOHEAL_FRESH_CHECKOUT}"
                        echo "AUTOHEAL_CLEAN_DEPENDENCY_ENV: ${params.AUTOHEAL_CLEAN_DEPENDENCY_ENV}"
                        echo "AUTOHEAL_INSTALL_FROM_LOCKFILE: ${params.AUTOHEAL_INSTALL_FROM_LOCKFILE}"
                        echo "AUTOHEAL_DOCKER_NO_CACHE: ${params.AUTOHEAL_DOCKER_NO_CACHE}"
                        echo "AUTOHEAL_CONNECTIVITY_CHECK: ${params.AUTOHEAL_CONNECTIVITY_CHECK}"
                        echo "AUTOHEAL_BACKOFF_SECONDS: ${params.AUTOHEAL_BACKOFF_SECONDS}"
                        echo '==============================================='
                    }

                    /*
                     * ------------------------------------------------
                     * AutoHeal Network Recovery
                     * ------------------------------------------------
                     *
                     * Kept before checkout because a real network
                     * failure can affect Git checkout itself.
                     */
                    if (
                        params.AUTOHEAL_RETRY &&
                        (
                            params.AUTOHEAL_ACTION == 'CONNECTIVITY_CHECK_BACKOFF' ||
                            params.AUTOHEAL_ACTION == 'CONNECTIVITY_CHECK_BACKOFF_AND_RETRY' ||
                            params.AUTOHEAL_CONNECTIVITY_CHECK
                        )
                    ) {

                        stage('AutoHeal - Network Recovery') {

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

                                # Connectivity check is advisory.
                                # The retry itself determines whether
                                # the pipeline has recovered.
                                exit 0
                            '''

                            echo 'AutoHeal: network recovery preparation completed.'
                        }
                    }

                    /*
                     * ------------------------------------------------
                     * AutoHeal Workspace Recovery
                     * ------------------------------------------------
                     */
                    if (
                        params.AUTOHEAL_RETRY &&
                        (
                            params.AUTOHEAL_ACTION == 'CLEAN_WORKSPACE' ||
                            params.AUTOHEAL_CLEAN_WORKSPACE ||
                            params.AUTOHEAL_FRESH_CHECKOUT
                        )
                    ) {

                        stage('AutoHeal - Workspace Recovery') {

                            echo 'AutoHeal: preparing clean workspace...'

                            deleteDir()

                            echo 'AutoHeal: workspace cleanup completed.'
                        }
                    }

                    echo 'Checking out source code...'

                    checkout scm

                    /*
                     * ------------------------------------------------
                     * Controlled Workspace Failure
                     * ------------------------------------------------
                     */
                    if (
                        !params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'WORKSPACE_FAILURE'
                    ) {

                        echo 'AutoHeal test: injecting workspace failure...'

                        sh '''
                            echo "ERROR: unable to create file in workspace"
                            exit 1
                        '''
                    }

                    echo 'Checkout completed.'
                }
            }
        }


        /*
         * ============================================================
         * TEST
         * ============================================================
         */
        stage('Test') {

            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                }
            }

            steps {

                script {

                    /*
                     * ------------------------------------------------
                     * AutoHeal Dependency Recovery
                     * ------------------------------------------------
                     */
                    if (
                        params.AUTOHEAL_RETRY &&
                        (
                            params.AUTOHEAL_ACTION == 'CLEAN_DEPENDENCY_ENV' ||
                            params.AUTOHEAL_CLEAN_DEPENDENCY_ENV
                        )
                    ) {

                        stage('AutoHeal - Dependency Recovery') {

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

                    /*
                     * ------------------------------------------------
                     * Controlled Dependency Failure
                     * ------------------------------------------------
                     */
                    if (
                        !params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'DEPENDENCY_FAILURE'
                    ) {

                        echo 'AutoHeal test: injecting dependency failure...'

                        sh '''
                            echo "ERROR: No matching distribution found for AUTOHEAL_DEPENDENCY_FAILURE"
                            exit 1
                        '''
                    }

                    /*
                     * ------------------------------------------------
                     * Controlled Network Failure
                     * ------------------------------------------------
                     *
                     * Only the initial build gets the injected
                     * failure. AutoHeal retry builds skip it.
                     */
                    if (
                        !params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'NETWORK_FAILURE'
                    ) {

                        echo 'AutoHeal test: injecting network failure...'

                        sh '''
                            echo "ERROR: Failed to connect to 127.0.0.1 port 9"
                            exit 1
                        '''
                    }

                    echo 'Running Python tests...'

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


        /*
         * ============================================================
         * SONARQUBE
         * ============================================================
         */
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


        /*
         * ============================================================
         * DOCKER BUILD
         * ============================================================
         */
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

                    /*
                     * ------------------------------------------------
                     * Controlled Docker Failure
                     * ------------------------------------------------
                     *
                     * Initial build only.
                     */
                    if (
                        !params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'DOCKER_FAILURE'
                    ) {

                        echo 'AutoHeal test: injecting Docker failure...'

                        sh '''
                            echo "ERROR: failed to build AUTOHEAL_DOCKER_FAILURE"
                            exit 1
                        '''
                    }

                    /*
                     * ------------------------------------------------
                     * AutoHeal Docker Recovery
                     * ------------------------------------------------
                     *
                     * This is now a visible Jenkins stage.
                     */
                    if (
                        params.AUTOHEAL_RETRY &&
                        (
                            params.AUTOHEAL_ACTION == 'INVALIDATE_DOCKER_CACHE' ||
                            params.AUTOHEAL_DOCKER_NO_CACHE
                        )
                    ) {

                        stage('AutoHeal - Docker Recovery') {

                            echo 'AutoHeal: Docker recovery started.'
                            echo 'AutoHeal: invalidating Docker build cache.'
                            echo 'AutoHeal: rebuilding image with --no-cache.'

                            sh """
                                docker build \
                                    --no-cache \
                                    -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                    .
                            """

                            echo 'AutoHeal: Docker recovery completed.'
                        }

                    } else {

                        /*
                         * Normal Docker build.
                         */
                        docker_build(
                            image: IMAGE_NAME,
                            tag: IMAGE_TAG
                        )
                    }
                }
            }
        }


        /*
         * ============================================================
         * TRIVY
         * ============================================================
         */
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


        /*
         * ============================================================
         * DOCKER PUSH
         * ============================================================
         */
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

                    /*
                     * ------------------------------------------------
                     * Controlled Registry Failure
                     * ------------------------------------------------
                     *
                     * Initial build only.
                     */
                    if (
                        !params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'REGISTRY_FAILURE'
                    ) {

                        echo 'AutoHeal test: injecting registry failure...'

                        sh '''
                            echo "ERROR: unauthorized: registry access denied"
                            exit 1
                        '''
                    }

                    /*
                     * ------------------------------------------------
                     * AutoHeal Registry Recovery
                     * ------------------------------------------------
                     *
                     * This is now a visible Jenkins stage.
                     *
                     * docker_push() is reused so your existing
                     * Docker Hub credential configuration remains
                     * unchanged.
                     */
                    if (
                        params.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_ACTION == 'RETRY_REGISTRY'
                    ) {

                        stage('AutoHeal - Registry Recovery') {

                            echo 'AutoHeal: registry recovery started.'
                            echo 'AutoHeal: re-authenticating with Docker Hub.'
                            echo 'AutoHeal: retrying image push.'

                            docker_push(
                                image: IMAGE_NAME,
                                tag: IMAGE_TAG,
                                credentialsId: 'dockerhub'
                            )

                            echo 'AutoHeal: registry recovery completed.'
                        }

                    } else {

                        /*
                         * Normal Docker push.
                         */
                        docker_push(
                            image: IMAGE_NAME,
                            tag: IMAGE_TAG,
                            credentialsId: 'dockerhub'
                        )
                    }
                }
            }
        }
    }


    /*
     * ================================================================
     * POST
     * ================================================================
     */
    post {

        failure {

            node('built-in') {

                script {

                    /*
                     * NEVER recursively notify AutoHeal for a
                     * retry build.
                     */
                    if (params.AUTOHEAL_RETRY) {

                        echo 'AutoHeal retry build failed.'
                        echo 'Skipping recursive AutoHeal webhook.'

                    } else {

                        sh(
                            script: '''
                                set +e

                                # Remove any stale response first.
                                rm -f /tmp/autoheal-response.json

                                HTTP_CODE=$(curl \
                                    --silent \
                                    --show-error \
                                    --output /tmp/autoheal-response.json \
                                    --write-out "%{http_code}" \
                                    --max-time 10 \
                                    -X POST \
                                    http://127.0.0.1:8000/webhook/jenkins \
                                    -H "Content-Type: application/json" \
                                    -H "X-AutoHeal-Secret: change-me" \
                                    --data-binary @- <<EOF
{
    "job_name": "${JOB_NAME}",
    "build_number": ${BUILD_NUMBER},
    "build_url": "${BUILD_URL}",
    "status": "FAILURE"
}
EOF
                                )

                                echo "AutoHeal HTTP status: ${HTTP_CODE}"

                                if [ -f /tmp/autoheal-response.json ]; then
                                    echo "AutoHeal response:"
                                    cat /tmp/autoheal-response.json
                                fi

                                if [ "${HTTP_CODE}" = "202" ] || [ "${HTTP_CODE}" = "200" ]; then
                                    echo "AutoHeal accepted the failure."
                                elif [ "${HTTP_CODE}" = "000" ]; then
                                    echo "WARNING: AutoHeal webhook could not be reached."
                                else
                                    echo "WARNING: AutoHeal returned HTTP ${HTTP_CODE}"
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
}