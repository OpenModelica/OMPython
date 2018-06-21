pipeline {
  agent {
    dockerfile {
      // Large image with full OpenModelica build dependencies; lacks omc and OMPython
      label 'linux'
      dir '.jenkins'
      additionalBuildArgs  '--pull'
    }
  }
  stages {
    stage('build') {
      parallel {
        stage('python2') {
          steps {
            sh 'python2 setup.py build'
            timeout(3) {
              sh 'python2 /usr/local/bin/py.test -v --junitxml py2.xml tests/*.py'
            }
            sh 'HOME="$PWD" python2 setup.py install --user'
            junit 'py2.xml'
          }
        }
        stage('python3') {
          steps {
            sh 'python3 setup.py build'
            timeout(3) {
              sh 'python3 /usr/local/bin/py.test -v --junitxml py3.xml tests/*.py'
            }
            sh 'HOME="$PWD" python3 setup.py install --user'
            junit 'py3.xml'
          }
        }
      }
    }
  }
}
