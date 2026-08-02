pipeline {
    agent none

    stages {

        stage('Checkout') {
            agent any

            steps {
                git branch: 'main',
                    url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'

                sh 'ls -la'
            }
        }

        stage('Test') {

            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root'
                }
            }

            steps {
                sh '''
                pip install -r requirements.txt

                pytest \
                  --junitxml=report.xml \
                  --cov=. \
                  --cov-report=xml
                '''
            }

            post {
                always {
                    junit 'report.xml'
                }
            }
        }

        stage('SonarQube Analysis') {

            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args '-u root:root'
                }
            }

            steps {

                withSonarQubeEnv('SonarQube') {

                    sh '''
                    ${SONAR_HOME}/bin/sonar-scanner
                    '''

                }

            }
        }
    }
}