
@Library(['Shared', 'AutoHeal']) _

pipeline {
    agent none

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    parameters {
        string(
            name: 'AUTOHEAL_ACTION',
            defaultValue: '',
            description: 'Internal AutoHeal routing value. Leave empty for normal builds.'
        )

        choice(
            name: 'AUTOHEAL_TEST_FAILURE',
            choices: [
                'NONE',
                'CODE_FAILURE',
                'WORKSPACE_FAILURE',
                'DEPENDENCY_FAILURE',
                'NETWORK_FAILURE',
                'UNKNOWN_FAILURE'
            ],
            description: 'Controlled fault-injection scenario for AutoHeal validation.'
        )
    }

    environment {
        IMAGE_NAME = 'anant2005ch/calculator'
        IMAGE_TAG = "${BUILD_NUMBER}"
        AUTOHEAL_TEST = 'true'
    }

    stages {

        // =====================================================
        // CHECKOUT
        // =====================================================

        stage('Checkout') {
            agent any

            steps {
                script {
                    // Run approved recovery actions at the appropriate stage.
                    autoheal(stage: 'checkout')

                    /*
                     * Controlled workspace fault:
                     * The Jenkins agent user creates a read-only directory
                     * and then attempts to write to it.
                     *
                     * Do not run this scenario as root on the host agent.
                     */
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'WORKSPACE_FAILURE'
                    ) {
                        echo 'AutoHeal test: inducing a real workspace permission failure.'

                        sh '''
                            set -eu

                            mkdir -p .autoheal-workspace-probe/locked
                            chmod 0555 .autoheal-workspace-probe/locked

                            echo "AUTOHEAL_WORKSPACE_FAILURE: workspace permission denied while writing probe" >&2

                            touch .autoheal-workspace-probe/locked/probe.txt
                        '''
                    }

                    /*
                     * Controlled network fault:
                     * Attempt a real HTTP connection to a local port where
                     * no service is expected to be listening.
                     *
                     * This does not disable the machine's network or change
                     * firewall settings.
                     */
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'NETWORK_FAILURE'
                    ) {
                        echo 'AutoHeal test: attempting a real HTTP connection to a controlled closed port.'

                        sh '''
                            set -eu

                            python3 - <<'PY'
import urllib.request

url = "http://127.0.0.1:9/autoheal-network-probe"
print(f"Attempting HTTP request to {url}")

with urllib.request.urlopen(url, timeout=3) as response:
    print(f"Unexpected response: {response.status}")
PY
                        '''
                    }

                    echo 'Checking out source code...'
                    checkout scm
                    echo 'Checkout completed.'
                }
            }
        }

        // =====================================================
        // TEST
        // =====================================================

        stage('Test') {
            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                    reuseNode true
                }
            }

            steps {
                script {
                    env.AUTOHEAL_WORKSPACE_OWNER = sh(
                        script: "stat -c '%u:%g' \"${WORKSPACE}\"",
                        returnStdout: true
                    ).trim()

                    echo "Jenkins workspace owner: ${env.AUTOHEAL_WORKSPACE_OWNER}"

                    // Run only the recovery action authorized by AutoHeal.
                    autoheal(stage: 'test')

                    sh '''
                        set -eu

                        if [ ! -d .venv ]; then
                            python -m venv .venv
                        fi

                        .venv/bin/python -m pip install \
                            --disable-pip-version-check \
                            -r requirements.txt
                    '''

                    /*
                     * Controlled dependency fault:
                     * Remove the test runner from the same virtual
                     * environment used by the test command.
                     */
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'DEPENDENCY_FAILURE'
                    ) {
                        echo 'AutoHeal test: removing pytest packages to create a real dependency failure.'

                        sh '''
                            set -eu
                            .venv/bin/python -m pip uninstall -y pytest pytest-cov
                        '''
                    }

                    /*
                     * Controlled code fault:
                     * A real failing assertion. AutoHeal should classify
                     * this as a code failure and avoid unsafe auto-fixes.
                     */
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'CODE_FAILURE'
                    ) {
                        echo 'AutoHeal test: triggering a controlled assertion failure.'

                        sh '''
                            set -eu

                            .venv/bin/python - <<'PY'
assert 2 + 3 == 9, (
    "Controlled code-failure test: "
    "expected an intentionally incorrect result"
)
PY
                        '''
                    }

                    /*
                     * Unknown fault:
                     * Used to verify that unrecognized failures are
                     * escalated instead of automatically remediated.
                     */
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'UNKNOWN_FAILURE'
                    ) {
                        sh '''
                            set -eu
                            echo "AUTOHEAL_DEMO_UNKNOWN: unexpected controller condition 7312" >&2
                            exit 1
                        '''
                    }

                    // Run tests using the same virtual environment
                    // that was installed and used for fault injection.
                    sh '''
                        set -eu

                        .venv/bin/python -m pytest \
                            -q \
                            --junitxml=report.xml \
                            --cov=. \
                            --cov-report=xml:coverage.xml
                    '''
                }
            }

            post {
                always {
                    script {
                        if (env.AUTOHEAL_WORKSPACE_OWNER?.trim()) {
                            echo "Restoring workspace ownership to ${env.AUTOHEAL_WORKSPACE_OWNER}..."

                            sh """
                                set -eu

                                if [ -d "${WORKSPACE}" ]; then
                                    chown -R \
                                        ${env.AUTOHEAL_WORKSPACE_OWNER} \
                                        "${WORKSPACE}"
                                fi
                            """

                            echo 'Workspace ownership restored.'
                        }
                    }

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

        // =====================================================
        // SONARQUBE ANALYSIS
        // =====================================================

        stage('SonarQube Analysis') {
            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args '-u root:root'
                    reuseNode true
                }
            }

            steps {
                script {
                    env.AUTOHEAL_SONAR_WORKSPACE_OWNER = sh(
                        script: "stat -c '%u:%g' \"${WORKSPACE}\"",
                        returnStdout: true
                    ).trim()

                    echo "Workspace owner before SonarQube: ${env.AUTOHEAL_SONAR_WORKSPACE_OWNER}"

                    sonarqube_analysis(
                        server: 'SonarQube',
                        scanner: 'sonar-scanner'
                    )
                }
            }

            post {
                always {
                    script {
                        if (env.AUTOHEAL_SONAR_WORKSPACE_OWNER?.trim()) {
                            echo 'Restoring workspace ownership after SonarQube...'

                            sh """
                                set -eu

                                if [ -d "${WORKSPACE}" ]; then
                                    chown -R \
                                        ${env.AUTOHEAL_SONAR_WORKSPACE_OWNER} \
                                        "${WORKSPACE}"
                                fi
                            """
                        }
                    }
                }
            }
        }

        // =====================================================
        // DOCKER BUILD
        // =====================================================

        stage('Docker Build') {
            agent {
                docker {
                    image 'docker:28-cli'
                    args '''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                    '''
                    reuseNode true
                }
            }

            steps {
                script {
                    // AutoHeal may request an approved cache-bypassing
                    // rebuild. A Docker daemon outage must be escalated.
                    autoheal(stage: 'docker')

                    docker_build(
                        image: env.IMAGE_NAME,
                        tag: env.IMAGE_TAG
                    )
                }
            }
        }

        // =====================================================
        // TRIVY SECURITY SCAN
        // =====================================================

        stage('Trivy Security Scan') {
            agent {
                docker {
                    image 'aquasec/trivy:latest'
                    args '''
                        --entrypoint=''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                    '''
                    reuseNode true
                }
            }

            steps {
                script {
                    trivy_scan(
                        image: env.IMAGE_NAME,
                        tag: env.IMAGE_TAG,
                        severity: 'CRITICAL,HIGH',
                        exitCode: '0'
                    )
                }
            }
        }

        // =====================================================
        // DOCKER PUSH
        // =====================================================

        stage('Docker Push') {
            agent {
                docker {
                    image 'docker:28-cli'
                    args '''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                    '''
                    reuseNode true
                }
            }

            steps {
                script {
                    // Recovery must never bypass registry authentication.
                    autoheal(stage: 'registry')

                    docker_push(
                        image: env.IMAGE_NAME,
                        tag: env.IMAGE_TAG,
                        credentialsId: 'dockerhub'
                    )
                }
            }
        }
    }

    // =====================================================
    // AUTOHEAL FAILURE HOOK
    // =====================================================

    post {
        failure {
            node('built-in') {
                script {
                    /*
                     * Report normal build failures to AutoHeal.
                     * The Shared Library must prevent recursive incident
                     * submission for recovery builds.
                     */
                    autoheal()
                }
            }
        }
    }
}
