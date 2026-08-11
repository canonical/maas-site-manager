import { authResolvers } from "./auth";
import { enrollmentRequestsResolvers } from "./enrollmentRequests";
import { imageResolvers } from "./images";
import { oidcResolvers } from "./oidc";
import { sitesResolvers } from "./sites";
import { tileHandler } from "./tiles";
import { tokensResolvers } from "./tokens";
import { usersResolvers } from "./users";

import { imageSourceResolvers } from "@/testing/resolvers/imageSources";
export const allResolvers = [
  authResolvers.login.handler(),
  enrollmentRequestsResolvers.listEnrollmentRequests.handler(),
  enrollmentRequestsResolvers.postEnrollmentRequests.handler(),
  imageResolvers.selectedImages.handler(),
  imageResolvers.selectableImages.handler(),
  imageResolvers.getAlternativesForImage.handler(),
  imageResolvers.addImageToSelection.handler(),
  imageResolvers.removeImageFromSelection.handler(),
  imageResolvers.uploadCustomImage.handler(),
  imageResolvers.deleteCustomImage.handler(),
  sitesResolvers.listSites.handler(),
  sitesResolvers.sitesCoordinates.handler(),
  sitesResolvers.getSite.handler(),
  sitesResolvers.deleteSites.handler(),
  sitesResolvers.updateSites.handler(),
  tileHandler,
  tokensResolvers.listTokens.handler(),
  tokensResolvers.deleteTokens.handler(),
  tokensResolvers.createTokens.handler(),
  tokensResolvers.exportTokens.handler(),
  usersResolvers.listUsers.handler(),
  usersResolvers.getUser.handler(),
  usersResolvers.updateUser.handler(),
  usersResolvers.getCurrentUser.handler(),
  usersResolvers.updateCurrentUser.handler(),
  usersResolvers.updateCurrentUserPassword.handler(),
  usersResolvers.deleteUser.handler(),
  usersResolvers.createUser.handler(),
  imageSourceResolvers.listImageSources.handler(),
  imageSourceResolvers.getImageSource.handler(),
  imageSourceResolvers.createImageSource.handler(),
  imageSourceResolvers.updateImageSource.handler(),
  imageSourceResolvers.deleteImageSource.handler(),
  oidcResolvers.getActiveProvider.handler(),
  oidcResolvers.createProvider.handler(),
  oidcResolvers.updateProvider.handler(),
];
