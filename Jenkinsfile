pipeline {
    agent any

    stages {
        stage('checkout') {
            steps {
                checkout scm
            }
        }

        stage('install dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Tests') {
            steps {
                sh 'pytest'
            }
        }

        stage('build docker image') {
            steps {
                sh 'docker build -t kellidan/flask-app:latest .'
            }
        }

        stage('push to docker hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-creds', 
                    usernameVariable: 'DOCKER-USER',
                    passwordVariable: 'DOCKER-PASS')]) 
                    {
                        sh ''' 
                        echo $DOCKER-PASS | docker login -u $DOCKER-USER --password-stdin 
                        docker push kellidan/flask-app:latest
                        '''
                }
            }
        }
    }
}