import { ContentSection } from "@canonical/maas-react-components";

import EnrollmentActions from "@/app/settings/views/Requests/components/EnrollmentActions";
import RequestsTable from "@/app/settings/views/Requests/components/RequestsTable";

const RequestsList = () => {
  return (
    <ContentSection>
      <ContentSection.Header>
        <EnrollmentActions />
      </ContentSection.Header>
      <ContentSection.Content>
        <RequestsTable />
      </ContentSection.Content>
    </ContentSection>
  );
};

export default RequestsList;
