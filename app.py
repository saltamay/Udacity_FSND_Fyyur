#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime, date
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
# db = SQLAlchemy(app)

# TODO: connect to a local postgresql database

migrate = Migrate(app, db)

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
  # Order venues and artists by time they are created and return only the top 10 result
  latest_venues=Venue.query.filter(Venue.timestamp.isnot(None)).order_by(Venue.timestamp).limit(10)
  latest_artists=Artist.query.filter(Artist.timestamp.isnot(None)).order_by(Artist.timestamp).limit(10)

  # Chcek if the results are empty. If so set the display property to false
  # This will prevent frontend to render empty Artists or Venues section
  if len(latest_venues.all()) == 0:
    latest_venues_data={
      "display": False,
      "list": latest_venues
    }
  else:
    latest_venues_data={
      "display": True,
      "list": latest_venues
    }
  
  if len(latest_artists.all()) == 0:
    latest_artists_data={
      "display": False,
      "list": latest_artists
    }
  else:
    latest_artists_data={
      "display": True,
      "list": latest_artists
    }
  return render_template('pages/home.html', venues=latest_venues_data, artists=latest_artists_data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # Dynamically create the areas list
  areas=[]
  venues=Venue.query.all()
  for venue in venues:
    inserted=False
    for area in areas:
      if area["city"] == venue.city and area["state"] == venue.state:
        area["venues"].append(venue)
        inserted=True
    if not inserted or len(areas) == 0:
      area = {
        "city": None,
        "state": None,
        "venues": []
      }
      area["city"]=venue.city
      area["state"]=venue.state
      area["venues"].append(venue)
      areas.append(area)
  return render_template('pages/venues.html', areas=areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  
  # Add an option to search venues through "City, State"
  if search_term.find(',') != -1:
    city=search_term.split(', ')[0]
    state=search_term.split(', ')[1].upper()
    if city.find(' '):
      city_word_list = []
      for word in city.split(' '):
        city_word_list.append(word.capitalize())
      city=' '.join(city_word_list)
    search_term=city + ', ' + state
    data=Venue.query.filter_by(city=city, state=state).all()
  else:
    data=Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue=Venue.query.filter_by(id=venue_id).first()
  venue.past_shows=[]
  venue.upcoming_shows=[]
  # Get all shows in this venue
  shows=Show.query.filter_by(venue_id=venue_id).order_by('start_time').all()
  # Get current date
  today=datetime.now().replace(microsecond=0)
  # Loop through the shows to find out whther they are past or future
  for show in shows:
    artist=Artist.query.get(show.artist_id)
    show.artist_name=artist.name
    show.artist_image_link=artist.image_link
    show_time = datetime.strptime(show.start_time,"%Y-%m-%d %H:%M:%S")
    if today >= show_time:
      venue.past_shows.append(show)
    else:
      venue.upcoming_shows.append(show)
  # Set the number of past and upcoming shows
  venue.past_shows_count=len(venue.past_shows)
  venue.upcoming_shows_count=len(venue.upcoming_shows)
  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error=False
  genres=[]
  genres.append(request.form.get("genres"))
  new_venue = {
    "name": request.form.get("name"),
    "city": request.form.get("city"), 
    "state": request.form.get("state"), 
    "address": request.form.get("address"), 
    "phone": request.form.get("phone"),
    "genres": genres,
    "facebook_link": request.form.get("facebook_link")
  }
  try:
    venue=Venue(name=new_venue["name"], city=new_venue["city"], state=new_venue["state"], address=new_venue["address"], phone=new_venue["phone"], genres=new_venue["genres"], facebook_link=new_venue["facebook_link"])
    db.session.add(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + new_venue['name'] + ' could not be listed.')
    return render_template('errors/500.html')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))

#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue=Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return None

#  Update Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  form.name.data=venue.name
  form.city.data=venue.city
  form.state.data=venue.state
  form.address.data=venue.address
  form.phone.data=venue.phone
  form.genres.data=venue.genres
  form.facebook_link.data=venue.facebook_link

  venue=Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error=False
  try:
    Venue.query.filter_by(id=venue_id).update(request.form)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # On unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    render_template('errors/500.html')
  else:
    # On successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' info was successfully updated!')
    return render_template('pages/home.html')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists=Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')\
  # Add an option to search through "City, State"
  if search_term.find(',') != -1:
    city=search_term.split(', ')[0]
    state=search_term.split(', ')[1].upper()
    if city.find(' '):
      city_word_list = []
      for word in city.split(' '):
        city_word_list.append(word.capitalize())
      city=' '.join(city_word_list)
    search_term=city + ', ' + state
    data=Artist.query.filter_by(city=city, state=state).all()
  else:
    data=Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
  
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the Artist table, using artist_id
  artist=Artist.query.filter_by(id=artist_id).first()
  artist.past_shows=[]
  artist.upcoming_shows=[]
  # Get all shows for this artist
  shows=Show.query.filter_by(artist_id=artist_id).order_by('start_time').all()
  # Get current date
  today=datetime.now().replace(microsecond=0)
  # Loop through the shows to find out whther they are past or future
  for show in shows:
    venue=Venue.query.get(show.venue_id)
    show.venue_name=venue.name
    show.venue_image_link=venue.image_link
    show_time = datetime.strptime(show.start_time,"%Y-%m-%d %H:%M:%S")
    if today >= show_time:
      artist.past_shows.append(show)
    else:
      artist.upcoming_shows.append(show)
  # Set the number of past and upcoming shows
  artist.past_shows_count=len(artist.past_shows)
  artist.upcoming_shows_count=len(artist.upcoming_shows)
  return render_template('pages/show_artist.html', artist=artist)

#  Update Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # TODO: populate form with fields from artist with ID <artist_id>
  form.name.data=artist.name
  form.city.data=artist.city
  form.state.data=artist.state
  form.phone.data=artist.phone
  form.genres.data=artist.genres
  form.facebook_link.data=artist.facebook_link

  artist=Artist.query.get(artist_id)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error=False
  try:
    Artist.query.filter_by(id=artist_id).update(request.form)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    render_template('errors/500.html')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' info was successfully updated!')
    return render_template('pages/home.html')
  return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new artist record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error=False
  genres=[]
  genres.append(request.form.get("genres"))
  new_artist = {
    "name": request.form.get("name"),
    "city": request.form.get("city"), 
    "state": request.form.get("state"), 
    "phone": request.form.get("phone"),
    "genres": genres,
    "facebook_link": request.form.get("facebook_link")
  }
  try:
    artist=Artist(name=new_artist["name"], city=new_artist["city"], state=new_artist["state"], phone=new_artist["phone"], genres=new_artist["genres"], facebook_link=new_artist["facebook_link"])
    db.session.add(artist)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    render_template('errors/500.html')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows=Show.query.all()
  # Loop through all shows and populate data
  data=[]
  for show in shows:
    # Get venue and artist info
    venue=Venue.query.get(show.venue_id)
    artist=Artist.query.get(show.artist_id)
    # Set venue and artist info
    show.venue_name=venue.name
    show.artist_name=artist.name
    show.artist_image_link=artist.image_link
    data.append(show)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  error=False
  artist_id=request.form['artist_id']
  venue_id=request.form['venue_id']
  start_time=request.form['start_time']
  try:
    new_show=Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(new_show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
    render_template('errors/500.html')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
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

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
