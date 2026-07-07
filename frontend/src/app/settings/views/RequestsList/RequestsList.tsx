import { ContentSection } from "@canonical/maas-react-components";

import EnrollmentActions from "@/app/settings/views/RequestsList/components/EnrollmentActions";
import RequestsTable from "@/app/settings/views/RequestsList/components/RequestsTable";

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
