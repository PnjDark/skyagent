Buffer's API is built with GraphQL. If you're new to GraphQL, we'd recommend the [official GraphQL documentation](https://graphql.org/learn/) to get familiar with the basics before diving in.

## Register for API Access

To get started with the Buffer API, you'll need a Buffer account and an API key. If you don't have an account yet, you can [sign up here](https://buffer.com/signup).

Once you have an account, head to [API settings](https://publish.buffer.com/settings/api) to create your API key.

## What the API supports

Your API key lets you perform actions against **your own Buffer account**. We currently support the following operations:

- Post Creation
- Post Deletion
- Post Retrieval
- Idea Creation
- Account Retrieval
- Organization Retrieval
- Channel Retrieval

## Endpoint

The Buffer GraphQL API is available at:

```
https://api.buffer.com
```

If you'd like to use a tool like Postman or another HTTP client, point your requests to the endpoint above and follow [Postman's GraphQL guide](https://learning.postman.com/docs/sending-requests/graphql/graphql-overview/) for setup.

## Authorization

Every request must include an `Authorization` header with your API key using the `Bearer` format.

<!-- AUTH_CODE_EXAMPLES -->

## Making your first request

Here's a quick query to fetch your account and organization:

<!-- FIRST_REQUEST_CODE_EXAMPLES -->

Once you have your organization ID, you can use it to fetch channels, posts, and other data for that organization.

Draft posts can be created using the createPost mutation with the `saveToDraft` argument set to `true`. When saving a post as a draft, there are several required arguments:

- The channel ID that the post is being created for

- The scheduling type to be used for the post (automatic or notification)

- The sharing mode to be used for the post (add the post to the queue, share it now or share it next)

- The content to be used when creating the Post

- The `saveToDraft` flag set to `true` to save the post as a draft instead of scheduling it

When a post is saved as a draft, the post status will be set to 'draft' instead of 'scheduled' and the post will not be published until explicitly scheduled.

When performing the mutation, the PostActionSuccess type can be used to retrieve the information for the Post that was created. Similarly, the MutationError will provide you with information on the error that was triggered when trying to create the post.

```graphql
mutation CreateDraftPost {
  createPost(input: {
    text: "Hello there, this is a draft post!",
    channelId: "some_channel_id",
    schedulingType: automatic,
    mode: addToQueue,
    saveToDraft: true
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
      }
    }
    ... on MutationError {
      message
    }
  }
}
```
