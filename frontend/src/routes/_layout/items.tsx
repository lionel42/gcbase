import {
  Box,
  Button,
  Container,
  Flex,
  FormLabel,
  Heading,
  Icon,
  Select,
  SkeletonText,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Textarea,
  Th,
  Thead,
  Tr,
  useColorModeValue,
  useDisclosure,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { FaBicycle, FaPaperPlane, FaPlus } from "react-icons/fa";
import { z } from "zod";

import {
  type ApiError,
  type ItemPublic,
  ItemsService,
  LocationsService,
  type LogCreate,
  type LogPublic,
} from "../../client";
import ActionsMenu from "../../components/Common/ActionsMenu";
import Navbar from "../../components/Common/Navbar";
import { PaginationFooter } from "../../components/Common/PaginationFooter.tsx";
import AddItem from "../../components/Items/AddItem";
import AddLocation from "../../components/Items/AddLocation";
import useCustomToast from "../../hooks/useCustomToast";
import { handleError } from "../../utils";

const itemsSearchSchema = z.object({
  page: z.number().catch(1),
});

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  validateSearch: (search) => itemsSearchSchema.parse(search),
});

const PER_PAGE = 5;

function getItemsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ItemsService.readItems({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["items", { page }],
  };
}

function getLocationsQuery() {
  return useQuery({
    queryFn: () => LocationsService.readLocations(),
    queryKey: ["locations"],
    placeholderData: (prevData) => prevData,
  });
}

function ItemDetails({ item }: { item: ItemPublic }) {
  const showToast = useCustomToast();

  if (!item) return null;

  const color = useColorModeValue("inherit", "ui.light");
  const [newLocation, setNewLocation] = useState<string | null>(null);
  const [newLogMessage, setNewLogMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const logsQuery = useQuery({
    queryKey: ["item_logs", item.id],
    queryFn: () => ItemsService.readItemLogs({ itemId: item.id }),
  });

  const locationsQuery = getLocationsQuery();

  const sendLogMutation = useMutation({
    mutationKey: ["sendLog", item.id],
    mutationFn: () => {
      if (!newLogMessage) {
        return Promise.reject(new Error("No log message provided"));
      }
      return ItemsService.createItemLog({
        requestBody: { item_id: item.id, message: newLogMessage },
      });
    },
    onSuccess: () => {
      // update the log list
      queryClient.invalidateQueries({ queryKey: ["item_logs", item.id] });
      showToast("Success!", "Log created successfully.", "success");
      setNewLogMessage("");
    },
    onError: (err: ApiError) => {
      console.log(err);
      handleError(err, showToast);
    },
  });

  const currentPage = Route.useSearch();

  const moveItemMutation = useMutation({
    mutationKey: ["moveItem", item.id],
    mutationFn: (newLocation: string) =>
      ItemsService.moveItem({ itemId: item.id, newLocation }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["item_logs", item.id] });
      queryClient.invalidateQueries({ queryKey: ["items", currentPage] });
    },
    onError: (err: ApiError) => {
      handleError(err, showToast);
    },
  });

  const formatLog = (log: LogPublic) => {
    return (
      <Flex py={2} color="inherit" direction="row" align="flex-start">
        <Text pr={2}>
          {log.date
            ? new Date(log.date).toLocaleString(undefined, {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
              })
            : "Invalid date"}
        </Text>
        <Text pr={4}>{log.operator_name}</Text>
        <Text>{log.message}</Text>
      </Flex>
    );
  };

  const addModal = useDisclosure();

  return (
    <>
      <Container maxW="full">
        <Box w={{ sm: "full", md: "50%" }}>
          <Text fontSize="xl" color={color} w="auto" isTruncated>
            <Text as="i"> {item?.type} </Text> :{" "}
            <Text as="b">{item?.title || "N/A"}</Text>
          </Text>
          <Text fontSize="sm" color="ui.dim" w="auto" isTruncated>
            {item?.id}
          </Text>
          <Text
            size="md"
            py={2}
            color={!item?.description ? "ui.dim" : "inherit"}
            isTruncated
          >
            {item?.description || "N/A"}
          </Text>

          <Text
            size="md"
            py={2}
            color={!item?.status ? "ui.dim" : "inherit"}
            isTruncated
          >
            <Text as="b"> Status </Text>:{" "}
            <Text as="i">{item?.status || "N/A"}</Text>
          </Text>

          <FormLabel color={color} htmlFor="location" fontWeight="bold">
            Location
          </FormLabel>
          {
            <Flex mt={4} gap={3}>
              <Select w="auto" onChange={(e) => setNewLocation(e.target.value)}>
                {locationsQuery.data &&
                  Object.entries(locationsQuery.data.locations).map(
                    ([id, name]) => (
                      <option key={id} value={id}>
                        {name}
                      </option>
                    )
                  )}
              </Select>
              <Button
                variant="primary"
                gap={1}
                fontSize={{ base: "sm", md: "inherit" }}
                onClick={() => {
                  newLocation && moveItemMutation.mutate(newLocation);
                }}
              >
                <Icon as={FaBicycle} />
                Move Item
              </Button>
              <Button
                variant="outline"
                gap={1}
                fontSize={{ base: "sm", md: "inherit" }}
                onClick={addModal.onOpen}
              >
                <Icon as={FaPlus} />
                New Location
              </Button>
              <AddLocation
                isOpen={addModal.isOpen}
                onClose={addModal.onClose}
              />
            </Flex>
          }

          <FormLabel color={color} htmlFor="logs" fontWeight="bold">
            Logs
          </FormLabel>
          {logsQuery.data && logsQuery.data.count > 0 ? (
            <>
              <Flex py={2} direction="row" align="flex-start">
                <Text pr={2} fontWeight="bold">
                  New Log:
                </Text>
                <Textarea
                  id="newLog"
                  value={newLogMessage || ""}
                  onChange={(e) => setNewLogMessage(e.target.value)}
                  // Register Ctrl + Enter to send the log
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.ctrlKey) {
                      sendLogMutation.mutate();
                    }
                  }}
                />
                <Button
                  variant="primary"
                  onClick={() => {
                    sendLogMutation.mutate();
                  }}
                >
                  <Icon as={FaPaperPlane} />
                </Button>
              </Flex>
              <Box maxH="200px" overflowY="auto">
                {logsQuery.data.logs.map((log) => formatLog(log))}
              </Box>
            </>
          ) : (
            <Text size="md" py={2} color="ui.dim">
              No logs available.
            </Text>
          )}
        </Box>
      </Container>
    </>
  );
}

function ItemsTable({
  onSelectItem,
}: {
  onSelectItem: (item: ItemPublic) => void;
}) {
  const queryClient = useQueryClient();
  const { page } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const setPage = (page: number) =>
    navigate({
      search: (prev: { [key: string]: string }) => ({ ...prev, page }),
    });

  const locationsQuery = getLocationsQuery();

  const {
    data: items,
    isPending,
    isPlaceholderData,
  } = useQuery({
    ...getItemsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  });

  const hasNextPage = !isPlaceholderData && items?.data.length === PER_PAGE;
  const hasPreviousPage = page > 1;

  useEffect(() => {
    if (hasNextPage) {
      queryClient.prefetchQuery(getItemsQueryOptions({ page: page + 1 }));
    }
  }, [page, queryClient, hasNextPage]);

  const columns = ["Title", "Description", "Location", "Type", "Actions"];

  return (
    <>
      <TableContainer>
        <Table size={{ base: "sm", md: "md" }}>
          <Thead>
            <Tr>
              {columns.map((column) => (
                <Th key={`column${column}`}>{column}</Th>
              ))}
            </Tr>
          </Thead>
          {isPending ? (
            <Tbody>
              <Tr>
                {columns.map((column) => (
                  <Td key={`empty_row${column}`}>
                    <SkeletonText noOfLines={1} paddingBlock="16px" />
                  </Td>
                ))}
              </Tr>
            </Tbody>
          ) : (
            <Tbody>
              {items?.data.map((item) => (
                <Tr
                  key={item.id}
                  opacity={isPlaceholderData ? 0.5 : 1}
                  onClick={() => onSelectItem(item)}
                  cursor="pointer"
                >
                  <Td isTruncated maxWidth="150px">
                    {item.title}
                  </Td>
                  <Td
                    color={!item.description ? "ui.dim" : "inherit"}
                    isTruncated
                    maxWidth="150px"
                  >
                    {item.description || "N/A"}
                  </Td>
                  <Td
                    color={!item.location_id ? "ui.dim" : "inherit"}
                    isTruncated
                    maxWidth="150px"
                  >
                    {item.location_id
                      ? locationsQuery.data?.locations[item.location_id] ||
                        "N/A"
                      : "N/A"}
                  </Td>
                  <Td
                    color={!item.type ? "ui.dim" : "inherit"}
                    isTruncated
                    maxWidth="150px"
                  >
                    {item.type || "N/A"}
                  </Td>
                  <Td>
                    <ActionsMenu type={"Item"} value={item} />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          )}
        </Table>
      </TableContainer>
      <PaginationFooter
        page={page}
        onChangePage={setPage}
        hasNextPage={hasNextPage}
        hasPreviousPage={hasPreviousPage}
      />
    </>
  );
}

function Items() {
  const [selectedItem, setSelectedItem] = useState<ItemPublic | null>(null);
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Items Management
      </Heading>
      {selectedItem && <ItemDetails item={selectedItem} />}

      <Navbar type={"Item"} addModalAs={AddItem} />
      <ItemsTable onSelectItem={setSelectedItem} />
    </Container>
  );
}
