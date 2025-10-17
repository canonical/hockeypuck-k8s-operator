# Manage admin keys in Hockeypuck

Admin keys are required by Hockeypuck to perform [privileged operations](https://hockeypuck.io/admin.html). This includes submitting signed requests over HTTP to replace or delete public keys from the keyserver. By default, the [hockeypuck-k8s](https://charmhub.io/hockeypuck-k8s) charm takes care of creating an admin key on startup, uploading it to the keyserver and setting the admin key fingerprint field in the Hockeypuck [configuration file](https://hockeypuck.io/configuration.html#:~:text=1.1.4.%20Remote%20administration). This ensures that the charm is ready for administrative operations without any manual setup.

However, you can supplement the default admin key by setting the `admin-keys` configuration value in the Hockeypuck charm with a custom admin key:

```bash
juju config hockeypuck-k8s admin-keys=$ADMIN_FINGERPRINT
```

For Hockeypuck to identify this fingerprint as an admin key, you must also upload the admin key to the keyserver:

```bash
# store the public key of admin in a file
gpg --armor --export $ADMIN_FINGERPRINT > public_key.asc

# upload the admin public key to the key server
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "keytext=$(cat public_key.asc)" http://$HOCKEYPUCK_URL/pks/add
```

## Use custom admin key for manual actions

The `block-keys` action provided by the Hockeypuck charm always uses the default admin key created at startup to perform administrative tasks. If you wish to perform manual administration using your custom admin key, you must follow the [Hockeypuck server administration guide](https://hockeypuck.io/admin.html).