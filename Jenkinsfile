pipeline {
  agent any
  stages {
    stage('build') {
      parallel {
        stage('python2') {
          agent {
            docker {
              image 'python:2'
            }
          }
          steps {
            sh 'cat /etc/resolv.conf'
            sh 'python2 setup.py build'
            sh 'python2 setup.py test'
            sh 'python2 setup.py install'
          }
        }
        stage('python3') {
          agent {
            docker {
              image 'python:3'
            }
          }
          steps {
            sh 'cat /etc/resolv.conf'
            sh 'python3 setup.py build'
            sh 'python3 setup.py test'
            sh 'python3 setup.py install'
          }
        }
      }
    }
  }
}
