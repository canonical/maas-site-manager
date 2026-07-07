import "@/styles/App.scss";
import { SidePanelContextProvider } from "@canonical/maas-react-components";
import { ToastNotificationProvider } from "@canonical/react-components";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthContextProvider } from "@/app/context";
import { BootSourceContextProvider } from "@/app/context/BootSourceContext";
import { RowSelectionContextProviders } from "@/app/context/RowSelectionContext";
import { SiteDetailsContextProvider } from "@/app/context/SiteDetailsContext";
import { UserSelectionContextProvider } from "@/app/context/UserSelectionContext";
import { basename } from "@/constants";
import routes from "@/routes";
import { createBrowserRouter, RouterProvider } from "@/utils/router";

const queryClient = new QueryClient();
const router = createBrowserRouter(routes, { basename });

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <SidePanelContextProvider>
        <AuthContextProvider>
          <RowSelectionContextProviders>
            <UserSelectionContextProvider>
              <SiteDetailsContextProvider>
                <BootSourceContextProvider>
                  <ToastNotificationProvider>
                    <RouterProvider router={router} />
                  </ToastNotificationProvider>
                </BootSourceContextProvider>
              </SiteDetailsContextProvider>
            </UserSelectionContextProvider>
          </RowSelectionContextProviders>
        </AuthContextProvider>
      </SidePanelContextProvider>
    </QueryClientProvider>
  );
};

export default App;
