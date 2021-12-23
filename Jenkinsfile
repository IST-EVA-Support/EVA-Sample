pipeline {
    agent { label 'linux && x86 && build' }

    stages {
        stage('Copy files') {
            steps {
                sh 'scrtips/copy.sh'
            }
        }
        
        stage('Archive files') {
            steps {
                sh 'scrtips/archive.sh'
            }
        }
        
        stage('Upload files') {
            steps {
                sh 'scrtips/upload.sh'
            }
        }
    }
}
