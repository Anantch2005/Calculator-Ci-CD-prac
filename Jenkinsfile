
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
                'FLAKY_TEST',
                'WORKSPACE_FAILURE',
                'DEPENDENCY_FAILURE',
                'CODE_FAILURE',
                'UNKNOWN_FAILURE'
            ],
            description: 'Demo only: intentionally trigger an AutoHeal failure.'
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
                    // Reset one-shot demo state only for a fresh manual build.
                    // Recovery builds carry AUTOHEAL_ACTION and preserve the
                    // recovery marker created after the approved action runs.
                    if (!(params.AUTOHEAL_ACTION ?: '').trim()) {
                        sh '''
                            rm -f .autoheal-demo-workspace-recovered \
                                  .autoheal-demo-dependency-recovered \
                                  .autoheal-demo-flaky-triggered
                        '''
                    }

                    // Recovery hook for workspace/checkout actions.
                    autoheal(stage: 'checkout')

                    if (params.AUTOHEAL_ACTION == 'CLEAN_WORKSPACE') {
                        writeFile file: '.autoheal-demo-workspace-recovered',
                                  text: 'Workspace cleanup ran before checkout.\n'
                    }

                    if (
                        params.AUTOHEAL_TEST_FAILURE == 'WORKSPACE_FAILURE' &&
                        !fileExists('.autoheal-demo-workspace-recovered')
                    ) {
                        echo 'Demo: creating a real workspace permission failure.'
                        sh '''
                            set -eu
                            mkdir -p .autoheal-demo-locked/locked
                            chmod 0555 .autoheal-demo-locked/locked
                            echo 'AUTOHEAL_WORKSPACE_FAILURE: permission denied writing workspace probe' >&2
                            echo 'probe' > .autoheal-demo-locked/locked/probe
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
                    image 'python:3.12.12'
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
                    autoheal(stage: 'test')

                    if (params.AUTOHEAL_ACTION == 'CLEAN_DEPENDENCY_ENV') {
                        writeFile file: '.autoheal-demo-dependency-recovered',
                                  text: 'Dependency environment was recreated from requirements.txt.\n'
                    }

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
                        params.AUTOHEAL_TEST_FAILURE == 'DEPENDENCY_FAILURE' &&
                        !fileExists('.autoheal-demo-dependency-recovered')
                    ) {
                        echo 'Demo: removing pytest packages to create a real dependency failure.'

                        sh '''
                            set -eu
                            .venv/bin/python -m pip uninstall -y pytest pytest-cov
                        '''
                    }

                    if (
                        params.AUTOHEAL_TEST_FAILURE == 'FLAKY_TEST' &&
                        !fileExists('.autoheal-demo-flaky-triggered')
                    ) {
                        writeFile file: '.autoheal-demo-flaky-triggered',
                                  text: 'The one-shot flaky failure has been injected.\n'
                        sh '''
                            echo "AUTOHEAL_FLAKY_TEST: simulated one-shot test infrastructure failure" >&2
                            exit 1
                        '''
                    }

                    if (params.AUTOHEAL_TEST_FAILURE == 'CODE_FAILURE') {
                        sh '''
                            python -c 'assert 2 + 3 == 9, "AUTOHEAL_DEMO_CODE_FAILURE: intentional assertion failure"'
                        '''
                    }

                    if (
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
                    args "--entrypoint='' -u root:root"
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
                    image 'docker:28.3.3-cli'
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
                    autoheal(stage: 'docker')

                    if (params.AUTOHEAL_ACTION in ['DOCKER_CACHE_BYPASS', 'DOCKER_CACHE_BYPASS_AND_RETRY', 'INVALIDATE_DOCKER_CACHE', 'INVALIDATE_DOCKER_CACHE_AND_RETRY']) {
                        echo 'AutoHeal recovery: building this image with --no-cache.'
                        sh '''
                            set -eu
                            docker build --no-cache \
                                --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
                                .
                        '''
                    } else {
                        docker_build(
                            image: env.IMAGE_NAME,
                            tag: env.IMAGE_TAG
                        )
                    }
                }
            }
        }

        // =====================================================
        // TRIVY
        // =====================================================

        stage('Trivy Security Scan') {
            agent {
                docker {
                    image 'aquasec/trivy:0.67.2'
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
                        exitCode: '1'
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
                    image 'docker:28.3.3-cli'
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
                    // Normal failed build: report incident.
                    // Recovery build: Shared Library should prevent
                    // recursive incident submission.
                    autoheal()
                }
            }
        }
    }
}

