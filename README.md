# git-sae-ops

## Building

```

docker build --tag git-sae-ops .

```


## Command Line

```
export GITHUB_TOKEN=""

export PROJECTSC_HOST=""
export PROJECTSC_TOKEN=""

export GIT_USER_EMAIL=""
export GIT_USER_USERNAME=""

bin/glclic hello

```

## Server

```
docker run --rm -ti \
  -p 4100:4000 \
  -e OAUTHLIB_INSECURE_TRANSPORT=1 \
  -v `pwd`/config/default.json:/app/config/default.json \
  -v `pwd`/audit:/audit \
  git-sae-ops

```

# Commands

## Onboard project

At a minimum, add an SRE project as a group:

```
./bin/glclic \
    --project project-A \
    project
```


Create a new repository in the SAE shares group and a corresponding one in the checkpoint group, and grant access to the appropriate groups.

```
./bin/glclic \
    --project project-A \
    --external_url https://github.com/ikethecoder/external-test-repo.git \
    project
```

OR

```
./bin/glclic \
    --project project-A \
    --repo somerepo \
    project
```

For repositories that are going to be private (exclusive to one SRE project), include the "--private" flag.  This will enable Issues as well as enforcing only one group associated with a repository.


## Export Files

### Prepare for export

Called when a Researcher is ready to export files from the SAE.

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    --external_url https://github.com/ikethecoder/external-test-repo.git \
    request-export
```

OR 

```
./bin/glclic \
    --branch develop \
    --external_url https://github.com/ikethecoder/external-test-repo.git \
    request-export
```


### Approve the export merge request

Typically performed by an output checker in Gitlab.

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    approve-export-merge

```

### Perform push to external repository

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    --external_url https://github.com/ikethecoder/external-test-repo.git \
    push-to-external
```

OR (the external_url is taken from a custom attribute set when 'request-export' is executed)

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    push-to-external
```


## Import Files

### Prepare for import

Called when a Researcher is ready to import files into the SAE.

```
./bin/glclic \
    --branch develop \
    --external_url https://github.com/ikethecoder/external-test-repo.git \
    request-import
```

### Approve the import merge request

Typically performed by an output checker in Gitlab.

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    approve-import-merge

```

### Perform push to sre repository

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    push-to-sae
```


## Other commands

### Cancel an Import

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    cancel-import
```

### Cancel an Export

```
./bin/glclic \
    --branch develop \
    --repo ikethecoder-external-test-repo \
    cancel-export
```


### Initial Setup

```
./bin/glclic \
    --hook "http://projectsc_group_sync:8080/api/gitlab/webhook" \
    init

./bin/glclic \
    --hook "http://projectsc_git_sae_ops:4000/v1/flow/webhook" \
    --token ""
    init
```