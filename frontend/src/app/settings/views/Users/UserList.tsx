import { ContentSection, MainToolbar, useSidePanel } from "@canonical/maas-react-components";
import { SearchBox } from "@canonical/react-components";

import useDebounce from "@/app/base/hooks/useDebouncedValue";
import { lazySidePanel } from "@/app/base/sidePanel";
import UsersTable from "@/app/settings/views/Users/components/UsersTable";

const UserAddForm = lazySidePanel(() => import("@/app/settings/views/Users/components/UserForm/UserAddForm"));

const UserList = () => {
  const { openSidePanel } = useSidePanel();

  const [searchText, setSearchText] = useState("");
  const debounceSearchText = useDebounce(searchText);

  const handleSearchInput = (inputValue: string) => {
    setSearchText(inputValue);
  };

  return (
    <ContentSection className="user-list">
      <ContentSection.Header>
        <MainToolbar>
          <MainToolbar.Title>Users</MainToolbar.Title>
          <MainToolbar.Controls>
            <SearchBox
              className="user-list__search"
              externallyControlled
              onChange={handleSearchInput}
              placeholder="Search"
            />
            <button
              onClick={() => {
                openSidePanel({ component: UserAddForm, title: "Add user" });
              }}
              type="button"
            >
              Add user
            </button>
          </MainToolbar.Controls>
        </MainToolbar>
      </ContentSection.Header>
      <ContentSection.Content>
        <UsersTable debounceSearchText={debounceSearchText} />
      </ContentSection.Content>
    </ContentSection>
  );
};

export default UserList;
