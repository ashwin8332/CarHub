from flask import redirect, url_for, flash, session, render_template
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo

class ForgotPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    submit = SubmitField('Send OTP')

class VerifyOTPForm(FlaskForm):
    otp = StringField('OTP', validators=[
        InputRequired(),
        Length(min=6, max=6, message='OTP must be 6 digits')
    ])
    new_password = PasswordField('New Password', validators=[
        InputRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        InputRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

def init_password_reset_routes(app, password_reset_manager):
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = ForgotPasswordRequestForm()
        if form.validate_on_submit():
            email = form.email.data
            try:
                if password_reset_manager.send_password_reset_email(email):
                    flash('An OTP has been sent to your email address.', 'success')
                    session['reset_email'] = email  # Store email for OTP verification
                    return redirect(url_for('verify_otp'))
                flash('Error sending email. Please check your email address and try again.', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
        return render_template('forgot_password.html', form=form)

    @app.route('/verify-otp', methods=['GET', 'POST'])
    def verify_otp():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if 'reset_email' not in session:
            return redirect(url_for('forgot_password'))
            
        form = VerifyOTPForm()
        if form.validate_on_submit():
            email = session['reset_email']
            otp = form.otp.data
            new_password = form.new_password.data
            
            success, message = password_reset_manager.reset_password(
                email, otp, new_password
            )
            
            if success:
                session.pop('reset_email', None)  # Clear stored email
                flash('Your password has been reset successfully.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
                
        return render_template('verify_otp.html', form=form)