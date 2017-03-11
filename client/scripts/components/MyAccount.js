import React from 'react';

import Firebase from 'firebase';

// Material Design stuff
import RaisedButton from 'material-ui/RaisedButton';
import Header from './Header';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Paper from 'material-ui/Paper';

/*
  MyAccount
  Let's us make <MyAccount/> elements
*/

var MyAccount = React.createClass({
  getInitialState: function() {
      return {
        'uid':null,
        'name':null,
        'photo':null
      }
  },

  componentWillMount: function() {
    var user = Firebase.auth().currentUser;
    if (user) {
      this.state.name = user.displayName;
      this.state.uid = user.uid;
      this.state.photo = user.photoURL;
      this.setState(this.state);
    }
  },

  triggerLogin : function() {
    var successfulLogin = this.successfulLogin;
    var provider = new Firebase.auth.GoogleAuthProvider();
    var auth = Firebase.auth().signInWithPopup(provider).then(function(result) {
      var user = result.user;
      successfulLogin(user);
    }).catch(function(error) {
      console.log("couldn't log in for some reason");
      console.log(error);
    });
  },

  triggerLogout : function() {
    var accountComponent = this;
    var auth = Firebase.auth().signOut().then(function() {
      accountComponent.state.name = null;
      accountComponent.state.uid = null;
      accountComponent.state.photo = null;
      accountComponent.setState(accountComponent.state);
    }, function(error) {
      console.log("couldn't log out for some reason");
      console.log(error);
    });
  },

  successfulLogin : function(user) {
    this.state.name = user.displayName;
    this.state.uid = user.uid;
    this.state.photo = user.photoURL;
    this.setState(this.state);
  },

  render : function() {
    var styles = {
      container: {
        textAlign: 'center',
        paddingTop: 20,
      },
    };

    var headline = "You're not logged in. Want to log in?";
    if (this.state.uid) {
      var headline = "Hey, you're logged in as " + this.state.name;
    }

    return (
      <div>
        <Header history={this.props.history}/>
        <MuiThemeProvider>
          <Paper style={{'width':'60%','margin':'25px auto'}} zDepth={2}>
          <div style={styles.container}>
            <h1>{headline}</h1>
            <div>
               <img style={{'width':'150px','height':'150px','display':this.state.uid ? 'inline' : 'none'}} src={this.state.photo}/>
            </div>
            <RaisedButton style={{'margin':'20px 20px 20px 20px'}}
              label="Log In"
              onClick={this.triggerLogin}
              primary={true}
            />
            <RaisedButton style={{'margin':'20px 20px 20px 20px'}}
              label="Log Out"
              onClick={this.triggerLogout}
              primary={true}
            />
          </div>
          </Paper>
        </MuiThemeProvider>
      </div>
    )
  }

});

export default MyAccount;