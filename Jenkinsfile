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
                'CLEAN_WORKSPACE',
                'CLEAN_DEPENDENCY_ENV',
                'INVALIDATE_DOCKER_CACHE',
                'CONNECTIVITY_CHECK_BACKOFF'
            ],
            description: 'Internal AutoHeal remediation action.'
        )

        booleanParam(
            name: 'AUTOHEAL_CLEAN_WORKSPACE',
            defaultValue: false,
            description: 'Clean the Jenkins workspace before retry.'
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
            description: 'Build Docker image without using cache.'
        )

        booleanParam(
            name: 'AUTOHEAL_CONNECTIVITY_CHECK',
            defaultValue: false,
            description: 'Run connectivity checks before retry.'
        )

        string(
            name: 'AUTOHEAL_BACKOFF_SECONDS',
            defaultValue: '0',
            description: 'Backoff before retry, in seconds.'
        )
    }

    environment {
        IMAGE_NAME = "anant2005/calculator"
        IMAGE_TAG = "${BUILD_NUMBER}"

        AUTOHEAL_TEST = "true"
    }

    stages {

        // ============================================================
        // AUTOHEAL WORKSPACE RECOVERY
        // ============================================================

        stage('AutoHeal - Workspace Recovery') {
            when {
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
                echo "AutoHeal: cleaning Jenkins workspace..."

                cleanWs(
                    deleteDirs: true,
                    disableDeferredWipeout: true,
                    notFailBuild: false
                )

                echo "AutoHeal: workspace cleanup completed."
            }
        }

        // ============================================================
        // AUTOHEAL DEPENDENCY RECOVERY
        // ============================================================

        stage('AutoHeal - Dependency Recovery') {
            when {
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
                echo "AutoHeal: preparing clean dependency environment..."

                sh '''
                    set -eux

                    rm -rf .venv

                    python -m venv .venv

                    . .venv/bin/activate

                    python -m pip install --upgrade pip

                    if [ -f requirements.txt ]; then
                        if [ "${AUTOHEAL_INSTALL_FROM_LOCKFILE}" = "true" ]; then
                            echo "AutoHeal: installing dependencies from requirements file."
                            pip install -r requirements.txt
                        else
                            echo "AutoHeal: installing dependencies."
                            pip install -r requirements.txt
                        fi
                    fi
                '''

                echo "AutoHeal: dependency recovery preparation completed."
            }
        }

        // ============================================================
        // AUTOHEAL NETWORK RECOVERY
        // ============================================================

        stage('AutoHeal - Network Recovery') {
            when {
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
                        sleep time: backoff, unit: 'SECONDS'
                    }

                    echo "AutoHeal: checking network connectivity..."

                    sh '''
                        set +e

                        echo "Checking DNS..."
                        getent hosts github.com || true

                        echo "Checking HTTPS connectivity..."
                        curl --silent --show-error --max-time 10 \
                            https://github.com \
                            -o /dev/null

                        STATUS=$?

                        echo "Connectivity check exit code: ${STATUS}"

                        exit 0
                    '''
                }
            }
        }
    }
}        