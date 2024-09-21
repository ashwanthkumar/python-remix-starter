# captureforms.com

A microsas that gives you an endpoint to which you can submit your forms from any web page. We collect all the data and then make it available for you to export them in CSV or JSON files and eventually build integrations that you can leverage from or as part as your form submission.

---

## Simplified DEV Experience

Below you'll find the readme instructions specific for running the Backend API and Frontend APP. We have a single unified script that enables you to start both together once you're inside a virtualenv loaded shell. So this is how the workflow looks:

```
# this is needed only the 1st time
$ python -m venv venv
$ source venv/bin/activate
# install nodev20 if not already
$ nvm install v20
$ nvm alias default v20
$ node run_dev.js

# Run manually if you added items to requirements.txt
$ pip install -r requirements.txt

# For changes in models
$ flask db migrate -m "Initial migration"
$ flask db upgrade
```

## API README

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run the database:
```
docker run --rm -v $PWD/db_data:/var/lib/postgresql/data -e PGDATA=/var/lib/postgresql/data/pg_data/ --name captureforms -p 5432:5432 -e POSTGRES_PASSWORD=sa -e POSTGRES_USER=sa -e POSTGRES_DB=captureforms postgres:16-alpine
```

3. Set up the database:
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. Run the application:
```
flask run -p 5001
```

During development, I prefer to use nodeman so it autorestarts the server so you can test the changes very quickly. Assuming you have the latest node in PATH, you can start it as follows:

```
npx nodemon --exec "flask run -p 5001"
```

## Database Migrations

To create a new migration after changing the database models:

```
flask db migrate -m "Description of changes"
```

To apply the migrations to the database:

```
flask db upgrade
```

To revert the last migration:

```
flask db downgrade
```


## UI README

# Welcome to Remix!

- 📖 [Remix docs](https://remix.run/docs)

## Development

Run the dev server:

```shellscript
npm run dev
```

## Deployment

First, build your app for production:

```sh
npm run build
```

Then run the app in production mode:

```sh
npm start
```

Now you'll need to pick a host to deploy it to.

### DIY

If you're familiar with deploying Node applications, the built-in Remix app server is production-ready.

Make sure to deploy the output of `npm run build`

- `build/server`
- `build/client`

## Styling

This template comes with [Tailwind CSS](https://tailwindcss.com/) already configured for a simple default starting experience. You can use whatever css framework you prefer. See the [Vite docs on css](https://vitejs.dev/guide/features.html#css) for more information.
