pipeline {
    agent { label 'linux && x86 && build' }

    stages {
        stage('Copy files') {
            steps {
                sh 'scripts/copy.sh'
            }
        }
        
        stage('Archive files') {
            steps {
                sh 'scripts/archive.sh'
            }
        }
        
        stage('Upload files') {
            steps {
                sh 'scripts/upload.sh'
            }
        }
    }
}
