@Library('Shared') _
@Library('AutoHeal') _


pipeline {

    agent none


    options {

        skipDefaultCheckout(
            true
        )

        timestamps()
    }


    parameters {

        /*
         * =====================================================
         * INTERNAL AUTOHEAL ACTION
         * =====================================================
         *
         * Normal build:
         *
         *     ""
         *
         * AutoHeal retry:
         *
         *     CLEAN_WORKSPACE
         *     CLEAN_DEPENDENCY_ENV
         *     INVALIDATE_DOCKER_CACHE
         *     CONNECTIVITY_CHECK_BACKOFF
         *     RETRY_REGISTRY
         *     RETRY
         *
         * This is the only AutoHeal parameter.
         */

        string(

            name:
                'AUTOHEAL_ACTION',

            defaultValue:
                '',

            description:
                'Internal AutoHeal routing value. Leave empty for normal builds.'
        )


        /*
         * =====================================================
         * DEMO FAILURE SELECTOR
         * =====================================================
         *
         * This is ONLY for your Calculator E2E demonstration.
         */

        choice(

            name:
                'AUTOHEAL_TEST_FAILURE',

            choices: [

                'NONE',

                'FLAKY_TEST',

                'WORKSPACE_FAILURE',

                'DEPENDENCY_FAILURE',

                'NETWORK_FAILURE',

                'DOCKER_FAILURE',

                'REGISTRY_FAILURE',

                'UNKNOWN_FAILURE'
            ],

            description:
                'Demo only: intentionally trigger an AutoHeal failure.'
        )
    }


    environment {

        IMAGE_NAME =
            'anant2005ch/calculator'

        IMAGE_TAG =
            "${BUILD_NUMBER}"

        AUTOHEAL_TEST =
            'true'
    }


    stages {


        // =====================================================
        // CHECKOUT
        // =====================================================

        stage('Checkout') {

            agent any


            steps {

                script {

                    /*
                     * On normal build:
                     *
                     *     no-op
                     *
                     * On AutoHeal retry:
                     *
                     *     sets AUTOHEAL_RETRY=true
                     *     performs workspace/network recovery
                     */

                    autoheal()


                    // -------------------------------------------------
                    // DEMO WORKSPACE FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'WORKSPACE_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting workspace failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_WORKSPACE_FAILURE: unable to prepare workspace" \
                                >&2

                            exit 1
                        '''
                    }


                    // -------------------------------------------------
                    // DEMO NETWORK FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'NETWORK_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting network failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_NETWORK_FAILURE: failed to connect to remote service" \
                                >&2

                            exit 1
                        '''
                    }


                    // -------------------------------------------------
                    // DEMO UNKNOWN FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'UNKNOWN_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting unknown failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_DEMO_UNKNOWN: unexpected controller condition 7312" \
                                >&2

                            exit 1
                        '''
                    }


                    echo(
                        'Checking out source code...'
                    )


                    checkout scm


                    echo(
                        'Checkout completed.'
                    )
                }
            }
        }


        // =====================================================
        // TEST
        // =====================================================

        stage('Test') {

            agent {

                docker {

                    image:
                        'python:3.12'

                    args:
                        '-u root:root'

                    reuseNode:
                        true
                }
            }


            steps {

                script {

                    /*
                     * Capture workspace ownership before
                     * running the Docker test container as root.
                     */

                    env.AUTOHEAL_WORKSPACE_OWNER =
                        sh(

                            script:
                                "stat -c '%u:%g' \"${WORKSPACE}\"",

                            returnStdout:
                                true
                        ).trim()


                    echo(
                        "Jenkins workspace owner: "
                        + "${env.AUTOHEAL_WORKSPACE_OWNER}"
                    )


                    // -------------------------------------------------
                    // DEMO DEPENDENCY FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'DEPENDENCY_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting dependency failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_DEPENDENCY_FAILURE: dependency resolution failed" \
                                >&2

                            exit 1
                        '''
                    }


                    // -------------------------------------------------
                    // AUTOHEAL DEPENDENCY RECOVERY
                    // -------------------------------------------------

                    if (

                        env.AUTOHEAL_ACTION
                            == 'CLEAN_DEPENDENCY_ENV'
                    ) {

                        echo(
                            'AutoHeal: creating a clean Python environment.'
                        )


                        sh '''
                            set -eux

                            rm -rf .venv

                            python -m venv .venv

                            . .venv/bin/activate

                            python -m pip install \
                                --upgrade \
                                pip \
                                setuptools \
                                wheel
                        '''
                    }


                    // -------------------------------------------------
                    // PYTHON TEST
                    // -------------------------------------------------

                    if (

                        env.AUTOHEAL_ACTION
                            == 'CLEAN_DEPENDENCY_ENV'
                    ) {

                        /*
                         * Put .venv/bin first in PATH so the existing
                         * generic python_test() uses the clean venv.
                         *
                         * Generic Shared library remains unchanged.
                         */

                        withEnv([
                            "PATH=${env.WORKSPACE}/.venv/bin:${env.PATH}"
                        ]) {

                            python_test(

                                requirements:
                                    'requirements.txt',

                                testCommand:
                                    'pytest',

                                junitReport:
                                    'report.xml',

                                coverage:
                                    true,

                                coverageFile:
                                    'coverage.xml'
                            )
                        }

                    } else {

                        python_test(

                            requirements:
                                'requirements.txt',

                            testCommand:
                                'pytest',

                            junitReport:
                                'report.xml',

                            coverage:
                                true,

                            coverageFile:
                                'coverage.xml'
                        )
                    }
                }
            }


            post {

                always {

                    script {

                        /*
                         * Root Docker test container can create
                         * root-owned files. Restore Jenkins ownership.
                         */

                        if (

                            env.AUTOHEAL_WORKSPACE_OWNER
                            ?.trim()
                        ) {

                            echo(
                                "Restoring workspace ownership to "
                                + "${env.AUTOHEAL_WORKSPACE_OWNER}..."
                            )


                            sh """
                                set -eux

                                if [ -d "${WORKSPACE}" ]; then

                                    chown -R \
                                        ${env.AUTOHEAL_WORKSPACE_OWNER} \
                                        "${WORKSPACE}"

                                fi
                            """


                            echo(
                                'Workspace ownership restored.'
                            )
                        }
                    }


                    junit(

                        testResults:
                            'report.xml',

                        allowEmptyResults:
                            true
                    )


                    archiveArtifacts(

                        artifacts:
                            'coverage.xml',

                        allowEmptyArchive:
                            true
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

                    image:
                        'sonarsource/sonar-scanner-cli:latest'

                    args:
                        '-u root:root'

                    reuseNode:
                        true
                }
            }


            steps {

                script {

                    /*
                     * Preserve your existing ownership protection.
                     */

                    env.AUTOHEAL_SONAR_WORKSPACE_OWNER =
                        sh(

                            script:
                                "stat -c '%u:%g' \"${WORKSPACE}\"",

                            returnStdout:
                                true
                        ).trim()


                    echo(
                        "Jenkins workspace owner before SonarQube: "
                        + "${env.AUTOHEAL_SONAR_WORKSPACE_OWNER}"
                    )


                    sonarqube_analysis(

                        server:
                            'SonarQube',

                        scanner:
                            'sonar-scanner'
                    )
                }
            }


            post {

                always {

                    script {

                        if (

                            env.AUTOHEAL_SONAR_WORKSPACE_OWNER
                            ?.trim()
                        ) {

                            echo(
                                'Restoring workspace ownership after SonarQube...'
                            )


                            sh """
                                set -eux

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

                    image:
                        'docker:28-cli'

                    args:
                        '''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                        '''

                    reuseNode:
                        true
                }
            }


            steps {

                script {

                    // -------------------------------------------------
                    // DEMO DOCKER FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'DOCKER_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting Docker failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_DOCKER_FAILURE: failed to connect to Docker daemon" \
                                >&2

                            exit 1
                        '''
                    }


                    // -------------------------------------------------
                    // AUTOHEAL DOCKER RECOVERY
                    // -------------------------------------------------

                    if (

                        env.AUTOHEAL_ACTION
                            == 'INVALIDATE_DOCKER_CACHE'
                    ) {

                        echo(
                            'AutoHeal: rebuilding Docker image without cache.'
                        )


                        sh """
                            set -eux

                            docker build \
                                --no-cache \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                .
                        """

                    } else {

                        docker_build(

                            image:
                                env.IMAGE_NAME,

                            tag:
                                env.IMAGE_TAG
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

                    image:
                        'aquasec/trivy:latest'

                    args:
                        '''
                        --entrypoint=''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                        '''

                    reuseNode:
                        true
                }
            }


            steps {

                script {

                    trivy_scan(

                        image:
                            env.IMAGE_NAME,

                        tag:
                            env.IMAGE_TAG,

                        severity:
                            'CRITICAL,HIGH',

                        exitCode:
                            '0'
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

                    image:
                        'docker:28-cli'

                    args:
                        '''
                        -u root:root
                        -v /var/run/docker.sock:/var/run/docker.sock
                        '''

                    reuseNode:
                        true
                }
            }


            steps {

                script {

                    // -------------------------------------------------
                    // DEMO REGISTRY FAILURE
                    // -------------------------------------------------

                    if (

                        !env.AUTOHEAL_RETRY

                        &&

                        params.AUTOHEAL_TEST_FAILURE
                            == 'REGISTRY_FAILURE'
                    ) {

                        echo(
                            'AutoHeal demo: '
                            + 'injecting registry failure.'
                        )


                        sh '''
                            echo \
                                "AUTOHEAL_REGISTRY_FAILURE: unauthorized registry access" \
                                >&2

                            exit 1
                        '''
                    }


                    // -------------------------------------------------
                    // AUTOHEAL REGISTRY RECOVERY
                    // -------------------------------------------------

                    if (

                        env.AUTOHEAL_ACTION
                            == 'RETRY_REGISTRY'
                    ) {

                        echo(
                            'AutoHeal: retrying Docker registry push.'
                        )


                        docker_push(

                            image:
                                env.IMAGE_NAME,

                            tag:
                                env.IMAGE_TAG,

                            credentialsId:
                                'dockerhub'
                        )

                    } else {

                        docker_push(

                            image:
                                env.IMAGE_NAME,

                            tag:
                                env.IMAGE_TAG,

                            credentialsId:
                                'dockerhub'
                        )
                    }
                }
            }
        }
    }


    // =========================================================
    // AUTOHEAL POST FAILURE HOOK
    // =========================================================

    post {

        failure {

            /*
             * agent none means the post block does not
             * automatically have an executor for shell steps.
             *
             * Run AutoHeal from your Jenkins built-in node.
             */

            node('built-in') {

                script {

                    autoheal()
                }
            }
        }
    }
}