pipeline {
    agent {
        docker {
            image 'python:3.12'
            args '-u root:root'
        }
    }

    tools {
        sonarRunner 'SonarScanner'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/Anantch2005/Calculator-Ci-CD-prac'
            }
        }

        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh '''
                pytest \
                --junitxml=report.xml \
                --cov=. \
                --cov-report=xml
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {

                withSonarQubeEnv('SonarQube') {

                    sh '''
                    sonar-scanner
                    '''

                }

            }
        }

    }

    post {
        always {
            junit 'report.xml'
        }
    }
}