import { MainToolbar } from "@canonical/maas-react-components";
import { Button, Notification } from "@canonical/react-components";

import EnrollmentNotification from "./EnrollmentNotification";

import { useEnrollmentRequestsAction } from "@/app/api/query/enrollmentRequests";
import RemoveButton from "@/app/base/components/RemoveButton";
import { useRowSelection } from "@/app/context";

const EnrollmentActions: React.FC = () => {
  const { rowSelection, clearRowSelection } = useRowSelection("requests");
  const selectedIds = Object.keys(rowSelection).map((id) => Number(id));
  const enrollmentRequestsMutation = useEnrollmentRequestsAction();
  const isActionDisabled = Object.keys(rowSelection).length === 0 || enrollmentRequestsMutation.isPending;
  const handleAccept = () => {
    enrollmentRequestsMutation.mutate(
      {
        body: {
          accept: true,
          ids: selectedIds,
        },
      },
      { onSuccess: clearRowSelection },
    );
  };
  const handleDeny = () => {
    enrollmentRequestsMutation.mutate(
      {
        body: {
          accept: false,
          ids: selectedIds,
        },
      },
      { onSuccess: clearRowSelection },
    );
  };

  return (
    <>
      <div className="enrollment-actions">
        {enrollmentRequestsMutation.isSuccess ? (
          <EnrollmentNotification {...enrollmentRequestsMutation.variables.body} />
        ) : null}
        {enrollmentRequestsMutation.isError ? (
          <Notification role="alert" severity="negative">
            There was an error processing enrollment request(s).
          </Notification>
        ) : null}
        <MainToolbar>
          <MainToolbar.Title>Enrollment requests</MainToolbar.Title>
          <MainToolbar.Controls>
            <RemoveButton disabled={isActionDisabled} label="Deny" onClick={handleDeny} type="button" />
            <Button appearance="positive" disabled={isActionDisabled} onClick={handleAccept} type="button">
              Accept
            </Button>
          </MainToolbar.Controls>
        </MainToolbar>
      </div>
    </>
  );
};

export default EnrollmentActions;
