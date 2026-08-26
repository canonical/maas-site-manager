export const getApiUrl = (path: string): string => {
  return `*/api/v1${path}`;
};

export const apiUrls = {
  login: getApiUrl("/login"),
  logout: getApiUrl("/logout"),
  sites: getApiUrl("/sites"),
  sitesCoordinates: getApiUrl("/sites/coordinates"),
  tokens: getApiUrl("/tokens"),
  tokensExport: getApiUrl("/tokens/export"),
  users: getApiUrl("/users"),
  enrollmentRequests: getApiUrl("/sites/pending"),
  currentUser: getApiUrl("/users/me"),
  imageSources: getApiUrl("/bootasset-sources"),
  selectedImages: getApiUrl("/selected-images"),
  selectableImages: getApiUrl("/selectable-images"),
  alternativeImages: getApiUrl("/image-sources"),
  addImageToSelection: getApiUrl("/selectable-images:select"),
  removeImageFromSelection: getApiUrl("/selected-images:remove"),
  removeImage: getApiUrl("/images:remove"),
  bootAssets: getApiUrl("/bootassets"),
  images: getApiUrl("/images"),
  removeImages: getApiUrl("/images:remove"),
  upstreamImages: getApiUrl("/images/upstream"),
  upstreamImageSource: getApiUrl("/images/upstream-source"),
  settings: getApiUrl("/settings"),
  externalAuth: getApiUrl("/external-auth"),
  externalAuthCallback: getApiUrl("/external-auth/callback"),
};
