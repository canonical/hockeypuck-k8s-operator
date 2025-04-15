# Manage GPG keys with Hockeypuck

Hockeypuck charm provides 2 main actions for database management: `block-keys` and `lookup-key`.

The `block-keys` action allows you to delete a list of fingerprints from the keyserver:
```bash
juju run hockeypuck-k8s/0 block-keys fingerprints=2CF6A6A3B93C138FD51037564415DC328A6C8E00,7EG5A6A3B93C138FD51037568415DC326A6C8F01 comment=R123
```
This will ensure that the public keys associated with the fingerprints `2CF6A6A3B93C138FD51037564415DC328A6C8E00` and `7EG5A6A3B93C138FD51037568415DC326A6C8F01` are deleted from the keyserver and added to the hockeypuck's [blocklist](https://hockeypuck.io/configuration.html#:~:text=the%20OpenPGP%20engine-,blacklist,-contains%20a%20list) to prevent the keys from being reconciled again.

The `lookup-key` action allows you to check if a key associated with the fingerprint is present in the keyserver or not:
```
juju run hockeypuck-k8s/0 lookup-key keyword=0x2CF6A6A3B93C138FD51037564415DC328A6C8E00
```

[note]
**Note**: 
The prefix `0x` must be prepended to the fingerprint when running the `lookup-key` action but must not be added while running the `block-keys` action.
[/note]

## Hockeypuck APIs

Apart from the above-mentioned actions, Hockeypuck application also provides APIs to interact with the keyserver database. The following endpoints are available:

### 1. /pks/lookup
**Purpose:**
Retrieve information about keys stored on the keyserver.

**Query Parameters:**
- op: The operation type, e.g., get, vindex, or index.
- search: The search term (e.g., key ID, fingerprint, email, or name).
- fingerprint: Optional. If on, returns full fingerprints instead of short key IDs.

**Example:**
```bash
curl "http://$HOCKEYPUCK_ADDRESS/pks/lookup?op=get&search=$FINGERPRINT&fingerprint=on"
```

### 2. /pks/add
**Purpose:**
Add a new public key to the keyserver.

**Example:**
```bash
# store the public key of admin in a file
gpg --armor --export $ADMIN_FINGERPRINT > public_key.asc

curl -X POST -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "keytext=$(cat public_key.asc)" http://$HOCKEYPUCK_URL/pks/add
```

### 3. /pks/replace
**Purpose:**
Replace an existing public key on the keyserver with a new one.

**Example:**
```bash
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "keytext=$(cat request.txt)" --data-urlencode "keysig=$(cat signature.asc)" http://$HOCKEYPUCK_URL/pks/replace
```
Refer to the [Hockeypuck Server Administration](https://hockeypuck.io/admin.html) for more information on how to generate the signature and the request.

### 4. /pks/delete (POST)
**Purpose:**
Delete a public key from the keyserver.

**Example:**
```bash
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "keytext=$(cat request.txt)" --data-urlencode "keysig=$(cat signature.asc)" http://$HOCKEYPUCK_URL/pks/delete
```

Refer to the [Hockeypuck Server Administration](https://hockeypuck.io/admin.html) for more information on how to generate the signature and the request.
