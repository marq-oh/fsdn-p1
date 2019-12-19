#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, json
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
#import psycopg2
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from datetime import datetime
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Venue model
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(500), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    show = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

# Artist model
class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(500), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String)
  created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  show = db.relationship('Show', backref='artist', lazy=True)

  def __repr__(self):
    return f'<Artist {self.id} {self.name}>'

# Show model
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
      return f'<Show {self.id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Queries to get latest 10 records for artists and venues
  recent_artist_data = Artist.query.order_by(db.desc(Artist.created_date)).limit(10)
  recent_venue_data = Venue.query.order_by(db.desc(Venue.created_date)).limit(10)

  return render_template('pages/home.html', recent_artists=recent_artist_data, recent_venues=recent_venue_data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Query to just get City and State to support grouping by City and State in view
  area_data = Venue.query.with_entities(Venue.city, Venue.state).distinct()

  # Query to get all venue data. Grouping by City and State to be done in view
  venue_data = Venue.query.all()

  return render_template('pages/venues.html', areas=area_data, venues=venue_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  term = request.form.get('search_term')
  response = Venue.query.filter(Venue.name.ilike('%{}%'.format(term))).all()

  return render_template('pages/search_venues.html', results=response, search_term=term)

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  venue_detail = Venue.query.get(venue_id)
  artist_detail = Artist.query.all()

  # Setting up query to be able to determine Upcoming vs Past shows based on current datetime
  current_time = datetime.utcnow()
  upcomingshows_data = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time >= current_time).all()
  pastshows_data = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time < current_time).all()

  return render_template('pages/show_venue.html', venue=venue_detail, artist=artist_detail, upcomingshows=upcomingshows_data, pastshows=pastshows_data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        # Convert list to string with commas so that genres list can be displayed properly in view
        selected_genres = request.form.getlist('genres')
        selected_genres = ','.join(map(str, selected_genres))
        cleaned_genres_list = selected_genres.translate({ord(i): None for i in '[]'})

        newVenue = Venue(name=request.form['name'],
                         city=request.form['city'],
                         state=request.form['state'],
                         address=request.form['address'],
                         phone=request.form['phone'],
                         genres=cleaned_genres_list,
                         facebook_link=request.form['facebook_link'])

        db.session.add(newVenue)
        db.session.commit()

        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
        db.session.rollback()

        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
      Show.query.filter_by(venue_id=venue_id).delete()
      Venue.query.filter_by(id=venue_id).delete()
      db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists_data = Artist.query.all()
  return render_template('pages/artists.html', artists=artists_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  term = request.form.get('search_term')
  response = Artist.query.filter(Artist.name.ilike('%{}%'.format(term))).all()

  return render_template('pages/search_artists.html', results=response, search_term=term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_detail = Artist.query.get(artist_id)
  venue_detail = Venue.query.all()

  # Setting up query to be able to determine Upcoming vs Past shows based on current datetime
  current_time = datetime.utcnow()
  upcomingshows_data = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time >= current_time).all()
  pastshows_data = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < current_time).all()

  return render_template('pages/show_artist.html', venue=venue_detail, artist=artist_detail, upcomingshows=upcomingshows_data, pastshows=pastshows_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_data = Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])


def edit_artist_submission(artist_id):
  try:
      # Convert list to string with commas so that genres list can be displayed properly in view
      selected_genres = request.form.getlist('genres')
      selected_genres = ','.join(map(str, selected_genres))
      cleaned_genres_list = selected_genres.translate({ord(i): None for i in '[]'})

      artist_q = Artist.query.get(artist_id)
      artist_q.name = request.form['name']
      artist_q.city = request.form['city']
      artist_q.state = request.form['state']
      artist_q.genres = cleaned_genres_list
      artist_q.facebook_link = request.form['facebook_link']

      db.session.commit()
      flash('Artist was successfully edited!')

  except:
      db.session.rollback()

      flash('An error occurred. Artist could not be edited.')

  finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_data = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
      # Convert list to string with commas so that genres list can be displayed properly in view
      selected_genres = request.form.getlist('genres')
      selected_genres = ','.join(map(str, selected_genres))
      cleaned_genres_list = selected_genres.translate({ord(i): None for i in '[]'})

      venue_q = Venue.query.get(venue_id)
      venue_q.name = request.form['name']
      venue_q.city = request.form['city']
      venue_q.state = request.form['state']
      venue_q.address = request.form['address']
      venue_q.phone = request.form['phone']
      venue_q.genres = cleaned_genres_list
      venue_q.facebook_link = request.form['facebook_link']

      db.session.commit()
      flash('Venue was successfully edited!')

  except:
      db.session.rollback()

      flash('An error occurred. Venue could not be edited.')

  finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
      # Convert list to string with commas so that genres list can be displayed properly in view
      selected_genres = request.form.getlist('genres')
      selected_genres = ','.join(map(str, selected_genres))
      cleaned_genres_list = selected_genres.translate({ord(i): None for i in '[]'})

      newArtist = Artist(name = request.form['name'],
                       city = request.form['city'],
                       state = request.form['state'],
                       phone = request.form['phone'],
                       genres = cleaned_genres_list,
                       facebook_link = request.form['facebook_link'])

      db.session.add(newArtist)
      db.session.commit()

      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
      db.session.rollback()

      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  finally:
      db.session.close()

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows_data = Show.query.all()
  venue_data = Venue.query.all()
  artist_data = Artist.query.all()

  return render_template('pages/shows.html', shows=shows_data, venue=venue_data, artist=artist_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
      newShow = Show(artist_id = request.form['artist_id'],
                     venue_id = request.form['venue_id'],
                     start_time = request.form['start_time'])

      db.session.add(newShow)
      db.session.commit()

      flash('Show was successfully listed!')

  except:
      db.session.rollback()

      flash('An error occurred. Show could not be listed.')

  finally:
      db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
    #app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
