pipeline {
    agent { label 'linux && x86 && build' }

    stages {
        stage('Copy files') {
            sh 'scrtips/copy.sh'
        }
        
        stage('Archive files') {
            sh 'scrtips/archive.sh'
        }
        
        stage('Upload files') {
            sh 'scrtips/upload.sh'
        }
    }
}
