export const COGNITO_CONFIG = {
  region: "us-east-1",
  userPoolId: import.meta.env.VITE_USER_POOL_ID || "us-east-1_fD99TyD9S",
  userPoolClientId:
    import.meta.env.VITE_USER_POOL_CLIENT_ID || "2a1dun36pjrsgdj3bg0plms81k",
  domain:
    import.meta.env.VITE_COGNITO_DOMAIN ||
    "samai-236578428550.auth.us-east-1.amazoncognito.com",
};

export const API_URL =
  import.meta.env.VITE_API_URL ||
  "https://weo3vfe321.execute-api.us-east-1.amazonaws.com/prod";
