pipeline {
    agent {
        docker {
            image 'python:3.12'
            args '-u root:root'
        }
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
                sh '''
                    pip install -r requirement.txt
                '''
            }
        }
        stage('Test') {
            steps {
                sh '''
                pytest
                --junitxml=report.xml \
                --cov=. \
                --cov-report=xml 
                '''
            }
        }
    }
    post {

        always {
            junit 'report.xml'
        }
    }
}