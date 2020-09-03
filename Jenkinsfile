pipeline {
  agent none
  stages {
    stage('test') {
      parallel {
        stage('python2') {
          agent {
            dockerfile {
              // Large image with full OpenModelica build dependencies; lacks omc and OMPython
              label 'linux'
              dir '.jenkins/python2'
              additionalBuildArgs '--pull'
            }
          }
          steps {
            sh 'python2 setup.py build'
            timeout(3) {
              sh 'python2 /usr/local/bin/py.test -v --junitxml py2.xml tests'
            }
            sh 'HOME="$PWD" python2 setup.py install --user'
            junit 'py2.xml'
          }
        }
        stage('python3') {
          agent {
            dockerfile {
              // Large image with full OpenModelica build dependencies; lacks omc and OMPython
              label 'linux'
              dir '.jenkins/python3'
              additionalBuildArgs '--pull'
            }
          }
          steps {
            sh 'python3 setup.py build'
            timeout(3) {
              sh 'python3 /usr/local/bin/py.test -v --junitxml py3.xml tests'
            }
            sh 'HOME="$PWD" python3 setup.py install --user'
            junit 'py3.xml'
          }
        }
      }
    }
  }
}
