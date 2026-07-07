import { ContentSection, MainToolbar, useSidePanel } from "@canonical/maas-react-components";
import { SearchBox } from "@canonical/react-components";

import useDebounce from "@/app/base/hooks/useDebouncedValue";
import { sidePanels } from "@/app/base/sidePanels";
import UsersTable from "@/app/settings/views/Users/components/UsersTable";

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
                openSidePanel(sidePanels.addUser);
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
