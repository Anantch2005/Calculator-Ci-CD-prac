@Library(['Shared', 'BuildSentry']) _

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
            description: 'Internal BuildSentry routing value. Leave empty for normal builds.'
        )

        choice(
            name: 'AUTOHEAL_TEST_FAILURE',
            choices: [
                'NONE',
                'FLAKY_TEST',
                'WORKSPACE_FAILURE',
                'DEPENDENCY_FAILURE',
                'NETWORK_FAILURE',
                'UNKNOWN_FAILURE'
            ],
            description: 'Demo only: intentionally trigger a BuildSentry failure.'
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
                    // Recovery hook for workspace/checkout actions.
                    buildsentry(stage: 'checkout')

                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'WORKSPACE_FAILURE'
                    ) {
                        echo 'Demo: injecting a workspace failure.'

                        sh '''
                            echo "AUTOHEAL_WORKSPACE_FAILURE: unable to create file in workspace" >&2
                            exit 1
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

                    // Execute the approved recovery before testing.
                    // The Shared Library owns the recovery commands.
                    buildsentry(stage: 'test')

                    sh '''
                        set -eu

                        if [ ! -d .venv ]; then
                            python -m venv .venv
                        fi

                        .venv/bin/python -m pip install \
                            --disable-pip-version-check \
                            -r requirements.txt
                    '''

                    // Demo only: remove test dependencies from the
                    // environment actually used by the test command.
                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'DEPENDENCY_FAILURE'
                    ) {
                        echo 'Demo: removing pytest packages to create a real dependency failure.'

                        sh '''
                            set -eu
                            .venv/bin/python -m pip uninstall -y pytest pytest-cov
                        '''
                    }

                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'FLAKY_TEST'
                    ) {
                        sh '''
                            echo "AUTOHEAL_FLAKY_TEST: simulated test failure" >&2
                            exit 1
                        '''
                    }

                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'NETWORK_FAILURE'
                    ) {
                        sh '''
                            echo "AUTOHEAL_NETWORK_FAILURE: Connection refused while reaching remote service" >&2
                            exit 1
                        '''
                    }

                    if (
                        !env.AUTOHEAL_RETRY &&
                        params.AUTOHEAL_TEST_FAILURE == 'UNKNOWN_FAILURE'
                    ) {
                        sh '''
                            echo "AUTOHEAL_DEMO_UNKNOWN: unexpected controller condition 7312" >&2
                            exit 1
                        '''
                    }

                    // The tests must use the same virtual environment
                    // that AutoHeal recovers.
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
        // SONARQUBE
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
                    // AutoHeal only runs an approved action here.
                    // A Docker daemon outage must be escalated.
                    buildsentry(stage: 'docker')

                    docker_build(
                        image: env.IMAGE_NAME,
                        tag: env.IMAGE_TAG
                    )
                }
            }
        }

        // =====================================================
        // TRIVY
        // =====================================================

        stage('Trivy Security Scan') {
            agent {
                docker {
                    image 'aquasec/trivy:latest'
                    args '''
                        --entrypoint=''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                        -v buildsentry_trivy_cache:/root/.cache/trivy
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
                    // Registry hook does not bypass authentication.
                    buildsentry(stage: 'registry')

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
                    // Normal failed build: report incident.
                    // Recovery build: Shared Library should prevent
                    // recursive incident submission.
                    buildsentry()
                }
            }
        }
    }
}