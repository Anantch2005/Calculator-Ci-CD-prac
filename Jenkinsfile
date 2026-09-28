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

        // Temporary test selector.
        // Keep NONE for normal builds.
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
        IMAGE_TAG  = "${BUILD_NUMBER}"

        AUTOHEAL_TEST = 'true'
    }

    stages {

        // ============================================================
        // CHECKOUT
        // ============================================================

        stage('Checkout') {

            agent any

            steps {

                script {

                    // ==================================================
                    // AUTOHEAL WORKSPACE RECOVERY
                    // Created only during an AutoHeal retry.
                    // ==================================================

                    if (
                        params.AUTOHEAL_RETRY &&
                        (
                            params.AUTOHEAL_ACTION == 'CLEAN_WORKSPACE' ||
                            params.AUTOHEAL_CLEAN_WORKSPACE
                        )
                    ) {

                        stage('AutoHeal - Workspace Recovery') {

                            echo 'AutoHeal: cleaning Jenkins workspace...'

                            cleanWs(
                                deleteDirs: true,
                                disableDeferredWipeout: true,
                                notFailBuild: false
                            )

                            echo 'AutoHeal: workspace cleanup completed.'
                        }
                    }

                    echo 'Checking out source code...'

                    checkout scm

                    // ==================================================
                    // TEST: WORKSPACE FAILURE
                    // Non-destructive failure injection.
                    // ==================================================

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

                    try {

                        // ==============================================
                        // AUTOHEAL DEPENDENCY RECOVERY
                        // ==============================================

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

                        // ==============================================
                        // AUTOHEAL NETWORK RECOVERY
                        // ==============================================

                        if (
                            params.AUTOHEAL_RETRY &&
                            (
                                params.AUTOHEAL_ACTION == 'CONNECTIVITY_CHECK_BACKOFF' ||
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

                                    exit 0
                                '''
                            }
                        }

                        // ==============================================
                        // TEST: DEPENDENCY FAILURE
                        // ==============================================

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

                        // ==============================================
                        // TEST: NETWORK FAILURE
                        // ==============================================

                        if (
                            !params.AUTOHEAL_RETRY &&
                            params.AUTOHEAL_TEST_FAILURE == 'NETWORK_FAILURE'
                        ) {

                            echo 'AutoHeal test: injecting network failure...'

                            sh '''
                                curl \
                                    --silent \
                                    --show-error \
                                    --fail \
                                    --max-time 2 \
                                    http://127.0.0.1:9
                            '''
                        }

                        // ==============================================
                        // EXISTING PYTHON TEST
                        // ==============================================

                        echo 'Running Python tests...'

                        python_test(
                            requirements: 'requirements.txt',
                            testCommand: 'pytest',
                            junitReport: 'report.xml',
                            coverage: true,
                            coverageFile: 'coverage.xml'
                        )

                    } finally {

                        // ==================================================
                        // IMPORTANT:
                        // Docker test container runs as root.
                        // Restore workspace ownership to the Jenkins user
                        // before the container exits.
                        //
                        // We discover the correct UID/GID from the workspace
                        // itself, so there is no hardcoded Jenkins UID.
                        // ==================================================

                        sh '''
                            OWNER="$(stat -c '%u:%g' . 2>/dev/null || true)"

                            if [ -n "$OWNER" ]; then
                                echo "Restoring workspace ownership to $OWNER"
                                chown -R "$OWNER" . 2>/dev/null || true
                            fi
                        '''
                    }
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

            post {

                always {

                    // Sonar may create .scannerwork as root.
                    sh '''
                        OWNER="$(stat -c '%u:%g' . 2>/dev/null || true)"

                        if [ -n "$OWNER" ]; then
                            chown -R "$OWNER" . 2>/dev/null || true
                        fi
                    '''
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

                    // ==============================================
                    // TEST: DOCKER FAILURE
                    // ==============================================

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

                    // ==============================================
                    // TEST: REGISTRY FAILURE
                    // ==============================================

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

                    // ==================================================
                    // VERY IMPORTANT
                    //
                    // A recovery build is already owned by the original
                    // AutoHeal incident. Do NOT send its failure back
                    // into AutoHeal again.
                    //
                    // This prevents:
                    //
                    // retry -> webhook -> retry -> webhook -> ...
                    // ==================================================

                    if (params.AUTOHEAL_RETRY) {

                        echo 'AutoHeal retry build failed.'
                        echo 'Skipping recursive AutoHeal webhook.'
                        echo 'Original AutoHeal incident will record the failed retry.'

                    } else {

                        sh(
                            script: '''
                                set +e

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
                                    echo
                                fi

                                case "${HTTP_CODE}" in

                                    200|202)
                                        echo "AutoHeal accepted the failure."
                                        ;;

                                    000)
                                        echo "WARNING: AutoHeal webhook could not be reached."
                                        ;;

                                    *)
                                        echo "WARNING: AutoHeal returned HTTP ${HTTP_CODE}"
                                        ;;

                                esac

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