pipeline {
    agent {
        docker {
            image 'ubuntu:latest'
            args '''
            -u root:root
            -v /var/lib/jenkins/tools:/var/lib/jenkins/tools
            '''
        }
    }
    environment {
        SONAR_HOME = tool 'SonarScanner'
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
                sh 'apt-get update && apt-get install -y python3-pip'
                sh 'pip3 install -r requirements.txt'
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
        stage('Check Java') {
            steps {
                sh '''
                apt-get update
                apt-get install -y openjdk-17-jre
                java -version
                '''
            }
            }

        stage('SonarQube Analysis') {
            steps {
                script {

                    withSonarQubeEnv('SonarQube') {
                        sh """
                        ${SONAR_HOME}/bin/sonar-scanner
                        """
                    }
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